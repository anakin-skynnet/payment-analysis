"""SQLModel entities and shared helpers for app tables (authorization events, decisions, experiments, incidents)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuthorizationEvent(SQLModel, table=True):
    """
    Persisted authorization outcomes (issuer/PSP result).

    In a real deployment this would be fed by Lakeflow streaming into Unity Catalog.
    For the scaffold, we keep it minimal but queryable for KPI dashboards.
    """

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)

    merchant_id: str = Field(index=True)
    amount_minor: int
    currency: str = Field(index=True)

    network: str | None = Field(default=None, index=True)
    card_bin: str | None = Field(default=None, index=True)
    issuer_country: str | None = Field(default=None, index=True)
    entry_mode: str | None = Field(default=None, index=True)

    # approved | declined
    result: str = Field(index=True)

    # raw decline (issuer/psp) + normalized taxonomy
    decline_code_raw: str | None = Field(default=None, index=True)
    decline_reason: str | None = Field(default=None, index=True)

    is_retry: bool = Field(default=False, index=True)
    attempt_number: int = Field(default=0, index=True)


class DecisionLog(SQLModel, table=True):
    """
    Audit log of decisioning (auth, retry, routing, decline remediation).
    """

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)

    audit_id: str = Field(default_factory=lambda: uuid4().hex, unique=True, index=True)
    decision_type: str = Field(index=True)

    request: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )
    response: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )


class Experiment(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)

    name: str = Field(index=True)
    description: str | None = None

    # draft | running | paused | stopped
    status: str = Field(default="draft", index=True)
    started_at: datetime | None = None
    ended_at: datetime | None = None


class ExperimentAssignment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)

    experiment_id: str = Field(index=True, foreign_key="experiment.id")
    subject_key: str = Field(index=True)
    variant: str = Field(index=True)


class Incident(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)

    category: str = Field(index=True)  # e.g. mid_failure, bin_anomaly, entry_mode
    key: str = Field(index=True)  # e.g. MID=..., BIN=..., route=...
    severity: str = Field(default="medium", index=True)  # low|medium|high
    status: str = Field(default="open", index=True)  # open|mitigating|resolved

    details: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )


class RemediationTask(SQLModel, table=True):
    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)

    incident_id: str | None = Field(default=None, index=True, foreign_key="incident.id")
    status: str = Field(default="open", index=True)  # open|in_progress|done|cancelled

    title: str
    action: str | None = None
    owner: str | None = None


class DecisionConfig(SQLModel, table=True):
    """
    Tunable decision parameters stored in Lakebase.

    Single-row-per-key config table. The DecisionEngine caches these values
    and refreshes every ~60 s so real-time tuning does not require a redeploy.
    """

    key: str = Field(primary_key=True)
    value: str
    description: str | None = None
    updated_at: datetime = Field(default_factory=utcnow)


class RetryableDeclineCode(SQLModel, table=True):
    """
    Configurable soft decline codes that qualify for Smart Retry.

    Each row maps a decline code to backoff timing and retry parameters.
    Managed by ops teams via the app UI; consumed by the retry policy.
    """

    code: str = Field(primary_key=True)
    label: str
    category: str = Field(default="soft", index=True)  # soft | transient | issuer
    default_backoff_seconds: int = Field(default=900)  # 15 min default
    max_attempts: int = Field(default=3)
    is_active: bool = Field(default=True, index=True)
    updated_at: datetime = Field(default_factory=utcnow)


class RoutePerformance(SQLModel, table=True):
    """
    Route performance snapshot (approval rate, latency, cost) per PSP route.

    Updated periodically from Gold views or real-time streaming aggregates.
    The routing policy uses these scores instead of hardcoded values.
    """

    route_name: str = Field(primary_key=True)
    approval_rate_pct: float = Field(default=50.0)
    avg_latency_ms: float = Field(default=500.0)
    cost_score: float = Field(default=0.5)  # 0 = cheapest, 1 = most expensive
    is_active: bool = Field(default=True, index=True)
    updated_at: datetime = Field(default_factory=utcnow)


class DecisionOutcome(SQLModel, table=True):
    """
    Feedback loop: links a decision (by audit_id) to its actual outcome.

    The app or downstream systems call POST /api/decisions/outcome to record
    whether an approved/retried/routed transaction was ultimately successful.
    This data feeds the learning loop for model retraining and rule tuning.
    """

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)

    audit_id: str = Field(index=True)  # links to DecisionLog.audit_id
    decision_type: str = Field(index=True)  # authentication | retry | routing
    outcome: str = Field(index=True)  # approved | declined | timeout | error
    outcome_code: str | None = None  # raw issuer/psp code
    outcome_reason: str | None = None
    latency_ms: int | None = None

    extra: dict[str, Any] = Field(
        default_factory=dict, sa_column=Column(JSON, nullable=False)
    )


class ProposedConfigChange(SQLModel, table=True):
    """
    Agent-proposed configuration changes for operator approval.

    Agents (e.g. Performance Recommender) write proposed changes here
    when they detect suboptimal config. An operator reviews and approves
    or rejects them in the UI, closing the loop: data → ML → agents → config → decisions.
    """

    id: str = Field(default_factory=lambda: uuid4().hex, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)

    source_agent: str = Field(index=True)  # e.g. "performance_recommender", "decline_analyst"
    change_type: str = Field(index=True)   # e.g. "decision_config", "decline_code", "route_performance"
    target_key: str                         # e.g. "risk_threshold_medium", route name, decline code
    current_value: str | None = None
    proposed_value: str
    rationale: str                          # Agent-generated explanation
    expected_impact_pct: float | None = None  # Expected approval rate improvement (%)
    confidence: float = Field(default=0.5)    # Agent confidence in the proposal

    # pending | approved | rejected | applied
    status: str = Field(default="pending", index=True)
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    applied_at: datetime | None = None

