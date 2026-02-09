"""API for approval rules: Lakebase (when configured) or Lakehouse. Used by ML and agents to accelerate approval rates."""

from __future__ import annotations

from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from ..dependencies import DatabricksServiceDep
from ..lakebase_config import (
    create_approval_rule_in_lakebase,
    delete_approval_rule_in_lakebase,
    get_approval_rule_by_id,
    get_approval_rules_from_lakebase,
    update_approval_rule_in_lakebase,
)

router = APIRouter(tags=["rules"])


class ApprovalRuleOut(BaseModel):
    """Approval rule as stored in the Lakehouse."""
    id: str
    name: str
    rule_type: str
    condition_expression: Optional[str] = None
    action_summary: str
    priority: int
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ApprovalRuleIn(BaseModel):
    """Payload to create an approval rule."""
    name: str = Field(min_length=1, max_length=500)
    rule_type: str = Field(..., pattern="^(authentication|retry|routing)$")
    action_summary: str = Field(min_length=1, max_length=2000)
    condition_expression: Optional[str] = Field(None, max_length=5000)
    priority: int = Field(default=100, ge=0, le=10000)
    is_active: bool = True


class ApprovalRuleUpdate(BaseModel):
    """Payload to update an approval rule (partial)."""
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    rule_type: Optional[str] = Field(None, pattern="^(authentication|retry|routing)$")
    action_summary: Optional[str] = Field(None, min_length=1, max_length=2000)
    condition_expression: Optional[str] = Field(None, max_length=5000)
    priority: Optional[int] = Field(None, ge=0, le=10000)
    is_active: Optional[bool] = None


def _rule_row_to_out(row: dict) -> ApprovalRuleOut:
    return ApprovalRuleOut(
        id=str(row["id"]),
        name=str(row["name"]),
        rule_type=str(row["rule_type"]),
        condition_expression=str(row["condition_expression"]) if row.get("condition_expression") else None,
        action_summary=str(row["action_summary"]),
        priority=int(row.get("priority", 100)),
        is_active=bool(row.get("is_active", True)),
        created_at=str(row["created_at"]) if row.get("created_at") else None,
        updated_at=str(row["updated_at"]) if row.get("updated_at") else None,
    )


def _rule_row_from_payload(rule_id: str, payload: ApprovalRuleIn) -> dict:
    """Build a rule dict from create payload for response (Lakebase path)."""
    return {
        "id": rule_id,
        "name": payload.name,
        "rule_type": payload.rule_type,
        "condition_expression": payload.condition_expression,
        "action_summary": payload.action_summary,
        "priority": payload.priority,
        "is_active": payload.is_active,
        "created_at": None,
        "updated_at": None,
    }


def _find_rule_by_id(rows: list[dict], rule_id: str) -> ApprovalRuleOut | None:
    """Return ApprovalRuleOut for rule_id if found in rows, else None."""
    for r in rows:
        if str(r.get("id")) == rule_id:
            return _rule_row_to_out(r)
    return None


@router.get("", response_model=list[ApprovalRuleOut], operation_id="listApprovalRules")
async def list_approval_rules(
    request: Request,
    service: DatabricksServiceDep,
    rule_type: Optional[str] = Query(None, description="Filter by rule_type: authentication, retry, or routing"),
    active_only: bool = Query(False, description="Return only active rules"),
    limit: int = Query(200, ge=1, le=500, description="Max number of rules to return"),
) -> list[ApprovalRuleOut]:
    """List approval rules from Lakebase (if available) or Lakehouse. ML and AI agents read these to accelerate approval rates."""
    runtime = getattr(request.app.state, "runtime", None)
    if runtime and runtime._db_configured():
        rows = get_approval_rules_from_lakebase(runtime, rule_type=rule_type, active_only=active_only, limit=limit)
        if rows is not None:
            return [_rule_row_to_out(r) for r in rows]
    rows = await service.get_approval_rules(rule_type=rule_type, active_only=active_only, limit=limit)
    return [_rule_row_to_out(r) for r in rows]


@router.post("", response_model=ApprovalRuleOut, operation_id="createApprovalRule")
async def create_approval_rule(
    request: Request,
    service: DatabricksServiceDep,
    payload: ApprovalRuleIn,
) -> ApprovalRuleOut:
    """Create an approval rule in Lakebase (when configured) or Lakehouse. Used by decisioning and AI agents."""
    rule_id = uuid4().hex
    runtime = getattr(request.app.state, "runtime", None)

    if runtime and runtime._db_configured():
        ok = create_approval_rule_in_lakebase(
            runtime,
            id=rule_id,
            name=payload.name,
            rule_type=payload.rule_type,
            action_summary=payload.action_summary,
            condition_expression=payload.condition_expression,
            priority=payload.priority,
            is_active=payload.is_active,
        )
        if ok:
            return _rule_row_to_out(_rule_row_from_payload(rule_id, payload))
        raise HTTPException(status_code=502, detail="Failed to write rule to Lakebase.")

    if not service.is_available:
        raise HTTPException(status_code=503, detail="Databricks Lakehouse unavailable; cannot write rules.")
    try:
        ok = await service.create_approval_rule(
            id=rule_id,
            name=payload.name,
            rule_type=payload.rule_type,
            action_summary=payload.action_summary,
            condition_expression=payload.condition_expression,
            priority=payload.priority,
            is_active=payload.is_active,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=f"Failed to write rule to Lakehouse: {e}")
    if not ok:
        raise HTTPException(status_code=502, detail="Failed to write rule to Lakehouse.")
    rows = await service.get_approval_rules(limit=1)
    out = _find_rule_by_id(rows, rule_id)
    return out or _rule_row_to_out(_rule_row_from_payload(rule_id, payload))


@router.patch("/{rule_id}", response_model=ApprovalRuleOut, operation_id="updateApprovalRule")
async def update_approval_rule(
    request: Request,
    service: DatabricksServiceDep,
    rule_id: str,
    payload: ApprovalRuleUpdate,
) -> ApprovalRuleOut:
    """Update an approval rule in Lakebase (when configured) or Lakehouse."""
    runtime = getattr(request.app.state, "runtime", None)

    if runtime and runtime._db_configured():
        result = update_approval_rule_in_lakebase(
            runtime,
            rule_id,
            name=payload.name,
            rule_type=payload.rule_type,
            condition_expression=payload.condition_expression,
            action_summary=payload.action_summary,
            priority=payload.priority,
            is_active=payload.is_active,
        )
        if result is None:
            raise HTTPException(status_code=502, detail="Failed to update rule in Lakebase.")
        if result is False:
            raise HTTPException(status_code=404, detail="Rule not found.")
        row = get_approval_rule_by_id(runtime, rule_id)
        if row:
            return _rule_row_to_out(row)
        raise HTTPException(status_code=404, detail="Rule not found after update.")

    if not service.is_available:
        raise HTTPException(status_code=503, detail="Databricks Lakehouse unavailable; cannot update rules.")
    try:
        ok = await service.update_approval_rule(
            rule_id,
            name=payload.name,
            rule_type=payload.rule_type,
            condition_expression=payload.condition_expression,
            action_summary=payload.action_summary,
            priority=payload.priority,
            is_active=payload.is_active,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=f"Failed to update rule in Lakehouse: {e}")
    if not ok:
        raise HTTPException(status_code=502, detail="Failed to update rule in Lakehouse.")
    rows = await service.get_approval_rules(limit=500)
    out = _find_rule_by_id(rows, rule_id)
    if out:
        return out
    raise HTTPException(status_code=404, detail="Rule not found after update.")


@router.delete("/{rule_id}", status_code=204, operation_id="deleteApprovalRule")
async def delete_approval_rule(request: Request, service: DatabricksServiceDep, rule_id: str) -> None:
    """Delete an approval rule from Lakebase (when configured) or Lakehouse."""
    runtime = getattr(request.app.state, "runtime", None)

    if runtime and runtime._db_configured():
        if delete_approval_rule_in_lakebase(runtime, rule_id):
            return
        raise HTTPException(status_code=502, detail="Failed to delete rule from Lakebase.")

    if not service.is_available:
        raise HTTPException(status_code=503, detail="Databricks Lakehouse unavailable; cannot delete rules.")
    try:
        ok = await service.delete_approval_rule(rule_id)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=f"Failed to delete rule from Lakehouse: {e}")
    if not ok:
        raise HTTPException(status_code=502, detail="Failed to delete rule from Lakehouse.")
