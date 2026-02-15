"""Proposed Config Changes API: agent-proposed config changes with operator approval workflow.

Agents propose changes (e.g. adjust thresholds, add decline codes, update routes).
Operators review, approve, or reject in the UI. Approved changes are applied to Lakebase.
This closes the loop: data → ML → agents → proposed config → operator approval → config → decisions.
"""

from __future__ import annotations

import logging
from typing import Any, Optional, cast

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import desc
from sqlmodel import select

from ..db_models import ProposedConfigChange, DecisionConfig, RetryableDeclineCode, RoutePerformance, utcnow
from ..dependencies import SessionDep

logger = logging.getLogger(__name__)
router = APIRouter(tags=["config-proposals"])


class ProposalIn(BaseModel):
    source_agent: str = Field(min_length=1)
    change_type: str = Field(min_length=1)
    target_key: str = Field(min_length=1)
    current_value: Optional[str] = None
    proposed_value: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    expected_impact_pct: Optional[float] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ReviewIn(BaseModel):
    action: str = Field(description="approve or reject")
    reviewed_by: Optional[str] = None


@router.get("", response_model=list[ProposedConfigChange], operation_id="listConfigProposals")
def list_proposals(
    session: SessionDep,
    limit: int = Query(100, ge=1, le=200),
    status: Optional[str] = Query(None, description="Filter by status: pending, approved, rejected, applied"),
) -> list[ProposedConfigChange]:
    limit = max(1, min(limit, 200))
    stmt = select(ProposedConfigChange).order_by(desc(cast(Any, ProposedConfigChange.created_at))).limit(limit)
    if status:
        stmt = stmt.where(ProposedConfigChange.status == status)
    return list(session.exec(stmt).all())


@router.post("", response_model=ProposedConfigChange, operation_id="createConfigProposal")
def create_proposal(payload: ProposalIn, session: SessionDep) -> ProposedConfigChange:
    proposal = ProposedConfigChange(
        source_agent=payload.source_agent,
        change_type=payload.change_type,
        target_key=payload.target_key,
        current_value=payload.current_value,
        proposed_value=payload.proposed_value,
        rationale=payload.rationale,
        expected_impact_pct=payload.expected_impact_pct,
        confidence=payload.confidence,
    )
    session.add(proposal)
    session.commit()
    session.refresh(proposal)
    return proposal


@router.post("/{proposal_id}/review", response_model=ProposedConfigChange, operation_id="reviewConfigProposal")
def review_proposal(proposal_id: str, payload: ReviewIn, session: SessionDep) -> ProposedConfigChange:
    proposal = session.get(ProposedConfigChange, proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if proposal.status != "pending":
        raise HTTPException(status_code=400, detail=f"Proposal is already {proposal.status}")

    action = payload.action.lower().strip()
    if action not in {"approve", "reject"}:
        raise HTTPException(status_code=422, detail="Action must be 'approve' or 'reject'")

    proposal.status = "approved" if action == "approve" else "rejected"
    proposal.reviewed_by = payload.reviewed_by
    proposal.reviewed_at = utcnow()

    # Auto-apply approved changes to Lakebase config tables
    if proposal.status == "approved":
        try:
            _apply_config_change(session, proposal)
            proposal.status = "applied"
            proposal.applied_at = utcnow()
        except Exception as e:
            logger.warning("Failed to apply config change %s: %s", proposal_id, e)
            # Keep as "approved" — can be retried

    session.add(proposal)
    session.commit()
    session.refresh(proposal)
    return proposal


def _apply_config_change(session: SessionDep, proposal: ProposedConfigChange) -> None:
    """Apply an approved config change to the appropriate Lakebase table."""
    if proposal.change_type == "decision_config":
        existing = session.get(DecisionConfig, proposal.target_key)
        if existing:
            existing.value = proposal.proposed_value
            existing.updated_at = utcnow()
        else:
            session.add(DecisionConfig(
                key=proposal.target_key,
                value=proposal.proposed_value,
                description=f"Applied from agent proposal: {proposal.rationale[:200]}",
            ))
    elif proposal.change_type == "decline_code":
        existing = session.get(RetryableDeclineCode, proposal.target_key)
        if existing:
            existing.default_backoff_seconds = int(proposal.proposed_value)
            existing.updated_at = utcnow()
        else:
            session.add(RetryableDeclineCode(
                code=proposal.target_key,
                label=f"Agent-proposed: {proposal.target_key}",
                default_backoff_seconds=int(proposal.proposed_value),
            ))
    elif proposal.change_type == "route_performance":
        existing = session.get(RoutePerformance, proposal.target_key)
        if existing:
            existing.approval_rate_pct = float(proposal.proposed_value)
            existing.updated_at = utcnow()
    else:
        logger.warning("Unknown change_type %s — skipping auto-apply", proposal.change_type)
