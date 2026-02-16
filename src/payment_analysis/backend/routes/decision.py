"""Decisioning API: real-time auth, retry, and routing decisions with A/B experiment support.

ML predictions (approval, risk, routing) are fetched from Databricks Model Serving
when the connection is available; otherwise mock predictions are returned.
Validate with GET /api/v1/health/databricks. See docs/GUIDE.md §10 (Data sources & code guidelines).
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import select

logger = logging.getLogger(__name__)

from ..db_models import DecisionLog, Experiment, ExperimentAssignment
from ..services.databricks_service import MockDataGenerator
from ..decisioning.engine import DecisionEngine
from ..decisioning.policies import (
    decide_authentication,
    decide_retry,
    decide_routing,
    serialize_context,
)
from ..decisioning.schemas import (
    AuthDecisionOut,
    DecisionContext,
    RetryDecisionOut,
    RoutingDecisionOut,
)
from ..dependencies import SessionDep, DatabricksServiceDep, RuntimeDep
from ..utils import is_mock_request as _is_mock_request

router = APIRouter(tags=["decisioning"])


def _get_or_assign_variant(
    session: SessionDep,
    experiment_id: str | None,
    subject_key: str,
) -> str | None:
    """Resolve A/B variant for this subject. If no assignment exists and experiment is assignable, auto-enroll with 50/50 control/treatment (deterministic by subject_key). Returns None if no experiment or experiment not assignable."""
    if not experiment_id or not subject_key:
        return None
    stmt = select(ExperimentAssignment).where(
        ExperimentAssignment.experiment_id == experiment_id,
        ExperimentAssignment.subject_key == subject_key,
    ).limit(1)
    assignment = session.exec(stmt).first()
    if assignment:
        return assignment.variant
    exp = session.get(Experiment, experiment_id)
    if not exp or exp.status not in {"running", "draft"}:
        return None
    variant = "treatment" if (hashlib.sha256(subject_key.encode()).digest()[-1] % 2 == 1) else "control"
    session.add(
        ExperimentAssignment(
            experiment_id=experiment_id,
            subject_key=subject_key,
            variant=variant,
        )
    )
    session.commit()
    return variant


def _with_ab(decision: Any, experiment_id: str | None, variant: str | None) -> dict[str, Any]:
    """Merge experiment_id and variant into decision response for logging and response."""
    out = decision.model_dump()
    if experiment_id is not None:
        out["experiment_id"] = experiment_id
    if variant is not None:
        out["variant"] = variant
    return out


class MLPredictionInput(BaseModel):
    """Input for ML model predictions."""
    amount: float
    fraud_score: float = 0.1
    device_trust_score: float = 0.8
    is_cross_border: bool = False
    retry_count: int = 0
    uses_3ds: bool = False
    merchant_segment: str = "retail"
    card_network: str = "visa"


class ApprovalPredictionOut(BaseModel):
    """Output from approval propensity model."""
    approval_probability: float
    should_approve: bool
    model_version: str


class RiskPredictionOut(BaseModel):
    """Output from risk scoring model."""
    risk_score: float
    is_high_risk: bool
    risk_tier: str


class RoutingPredictionOut(BaseModel):
    """Output from smart routing model."""
    recommended_solution: str
    confidence: float
    alternatives: list[str]


class RetryPredictionOut(BaseModel):
    """Output from smart retry model."""
    should_retry: bool
    retry_success_probability: float
    model_version: str


async def _engine_decide(
    decision_type: str,
    ctx: DecisionContext,
    session: SessionDep,
    service: DatabricksServiceDep,
    runtime: RuntimeDep,
) -> AuthDecisionOut | RetryDecisionOut | RoutingDecisionOut:
    """Route a decision through DecisionEngine (ML + rules + Lakebase config) with graceful fallback.

    When the engine is available (Lakebase + Databricks Service configured), decisions
    benefit from:
    - Tunable thresholds from ``DecisionConfig`` (Lakebase)
    - Retryable decline codes from ``RetryableDeclineCode`` (Lakebase)
    - Route performance scores from ``RoutePerformance`` (Lakebase)
    - ML model enrichment (risk, approval, retry, routing)
    - Rule evaluation from ``approval_rules`` (Lakebase)
    - Online features written for the learning loop

    When Lakebase is not configured (e.g. local dev), falls back to pure-policy heuristics.
    """
    subject_key = ctx.subject_key or ctx.merchant_id
    variant = _get_or_assign_variant(session, ctx.experiment_id, subject_key)
    variant = variant if variant is not None else "control"

    # Try data-driven engine (Lakebase + ML + rules)
    try:
        engine = DecisionEngine(session=session, service=service, runtime=runtime)
        if decision_type == "authentication":
            decision = await engine.decide_authentication(ctx, variant=variant)
        elif decision_type == "retry":
            decision = await engine.decide_retry(ctx, variant=variant)
        elif decision_type == "routing":
            decision = await engine.decide_routing(ctx, variant=variant)
        else:
            raise ValueError(f"Unknown decision type: {decision_type}")
    except Exception as exc:
        # Graceful fallback to pure-policy heuristics (no ML, no rules, no Lakebase)
        logger.debug("DecisionEngine unavailable (%s), falling back to policies: %s", decision_type, exc)
        if decision_type == "authentication":
            decision = decide_authentication(ctx, variant=variant)
        elif decision_type == "retry":
            decision = decide_retry(ctx, variant=variant)
        else:
            decision = decide_routing(ctx, variant=variant)

    response = _with_ab(decision, ctx.experiment_id, variant)
    session.add(
        DecisionLog(
            audit_id=decision.audit_id,
            decision_type=decision_type,
            request=serialize_context(ctx),
            response=response,
        )
    )
    session.commit()
    return decision


@router.post(
    "/authentication", response_model=AuthDecisionOut, operation_id="decideAuthentication"
)
async def authentication(
    ctx: DecisionContext,
    session: SessionDep,
    service: DatabricksServiceDep,
    runtime: RuntimeDep,
) -> AuthDecisionOut:
    result = await _engine_decide("authentication", ctx, session, service, runtime)
    return result  # type: ignore[return-value]


@router.post("/retry", response_model=RetryDecisionOut, operation_id="decideRetry")
async def retry(
    ctx: DecisionContext,
    session: SessionDep,
    service: DatabricksServiceDep,
    runtime: RuntimeDep,
) -> RetryDecisionOut:
    result = await _engine_decide("retry", ctx, session, service, runtime)
    return result  # type: ignore[return-value]


@router.post("/routing", response_model=RoutingDecisionOut, operation_id="decideRouting")
async def routing(
    ctx: DecisionContext,
    session: SessionDep,
    service: DatabricksServiceDep,
    runtime: RuntimeDep,
) -> RoutingDecisionOut:
    result = await _engine_decide("routing", ctx, session, service, runtime)
    return result  # type: ignore[return-value]


# -- P3 #17: Read decision config thresholds ---


class DecisionConfigOut(BaseModel):
    """Current decision configuration thresholds (from Lakebase or defaults)."""
    risk_threshold_high: float
    risk_threshold_medium: float
    retry_max_attempts_control: int
    retry_max_attempts_treatment: int
    ml_enrichment_enabled: bool
    rule_engine_enabled: bool
    routing_domestic_country: str


@router.get(
    "/config",
    response_model=DecisionConfigOut,
    operation_id="getDecisionConfigThresholds",
)
async def get_decision_config(
    session: SessionDep,
    service: DatabricksServiceDep,
    runtime: RuntimeDep,
) -> DecisionConfigOut:
    """Get current decision engine configuration (thresholds and flags)."""
    try:
        engine = DecisionEngine(session=session, service=service, runtime=runtime)
        params = engine._load_config()
        return DecisionConfigOut(
            risk_threshold_high=params.risk_threshold_high,
            risk_threshold_medium=params.risk_threshold_medium,
            retry_max_attempts_control=params.retry_max_attempts_control,
            retry_max_attempts_treatment=params.retry_max_attempts_treatment,
            ml_enrichment_enabled=params.ml_enrichment_enabled,
            rule_engine_enabled=params.rule_engine_enabled,
            routing_domestic_country=params.routing_domestic_country,
        )
    except Exception as exc:
        logger.warning("Failed to load decision config: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# -- P0 #2: Feedback loop – record decision outcomes ---


class DecisionOutcomeIn(BaseModel):
    """Record the actual outcome of a previous decision (closes the feedback loop)."""
    audit_id: str
    decision_type: str
    outcome: str  # "approved", "declined", "timeout", etc.
    outcome_code: str | None = None
    outcome_reason: str | None = None
    latency_ms: int | None = None
    metadata: dict | None = None


class DecisionOutcomeOut(BaseModel):
    accepted: bool
    message: str


@router.post(
    "/outcome",
    response_model=DecisionOutcomeOut,
    operation_id="recordDecisionOutcome",
)
async def record_outcome(
    body: DecisionOutcomeIn,
    session: SessionDep,
    service: DatabricksServiceDep,
    runtime: RuntimeDep,
) -> DecisionOutcomeOut:
    """Record the actual outcome of a previous decision for the learning loop.

    This closes the feedback loop: Decision → Outcome → Retrain → Better Decisions.
    Without this, A/B experiments can't compute lift and models can't improve.
    """
    try:
        engine = DecisionEngine(session=session, service=service, runtime=runtime)
        ok = engine.record_outcome(
            audit_id=body.audit_id,
            decision_type=body.decision_type,
            outcome=body.outcome,
            outcome_code=body.outcome_code,
            outcome_reason=body.outcome_reason,
            latency_ms=body.latency_ms,
            metadata=body.metadata,
        )
        if ok:
            return DecisionOutcomeOut(accepted=True, message="Outcome recorded for learning loop.")
        return DecisionOutcomeOut(accepted=False, message="Engine could not persist outcome (session unavailable).")
    except Exception as exc:
        logger.warning("Failed to record decision outcome: %s", exc)
        return DecisionOutcomeOut(accepted=False, message=f"Error: {exc}")


# ML Model Serving Endpoints


@router.post(
    "/ml/approval",
    response_model=ApprovalPredictionOut,
    operation_id="predictApproval",
)
async def predict_approval(
    request: Request,
    service: DatabricksServiceDep,
    features: MLPredictionInput,
) -> ApprovalPredictionOut:
    """Get approval probability from ML model serving endpoint. Mock when toggle is on."""
    if _is_mock_request(request):
        result = MockDataGenerator.approval_prediction(features.model_dump())
        return ApprovalPredictionOut(**{k: v for k, v in result.items() if k != "_source"})
    try:
        result = await service.call_approval_model(features.model_dump())
    except Exception as exc:
        logger.exception("Approval model prediction failed")
        raise HTTPException(status_code=502, detail=f"ML model error: {exc}") from exc
    return ApprovalPredictionOut(**result)


@router.post(
    "/ml/risk",
    response_model=RiskPredictionOut,
    operation_id="predictRisk",
)
async def predict_risk(
    request: Request,
    service: DatabricksServiceDep,
    features: MLPredictionInput,
) -> RiskPredictionOut:
    """Get risk score from ML model serving endpoint. Mock when toggle is on."""
    if _is_mock_request(request):
        result = MockDataGenerator.risk_prediction(features.model_dump())
        return RiskPredictionOut(**{k: v for k, v in result.items() if k != "_source"})
    try:
        result = await service.call_risk_model(features.model_dump())
    except Exception as exc:
        logger.exception("Risk model prediction failed")
        raise HTTPException(status_code=502, detail=f"ML model error: {exc}") from exc
    return RiskPredictionOut(**result)


@router.post(
    "/ml/routing",
    response_model=RoutingPredictionOut,
    operation_id="predictRouting",
)
async def predict_routing(
    request: Request,
    service: DatabricksServiceDep,
    features: MLPredictionInput,
) -> RoutingPredictionOut:
    """Get optimal routing recommendation from ML model. Mock when toggle is on."""
    if _is_mock_request(request):
        result = MockDataGenerator.routing_prediction(features.model_dump())
        return RoutingPredictionOut(**{k: v for k, v in result.items() if k != "_source"})
    try:
        result = await service.call_routing_model(features.model_dump())
    except Exception as exc:
        logger.exception("Routing model prediction failed")
        raise HTTPException(status_code=502, detail=f"ML model error: {exc}") from exc
    return RoutingPredictionOut(**result)


@router.post(
    "/ml/retry",
    response_model=RetryPredictionOut,
    operation_id="predictRetry",
)
async def predict_retry(
    request: Request,
    service: DatabricksServiceDep,
    features: MLPredictionInput,
) -> RetryPredictionOut:
    """Get retry success likelihood from smart retry model. Mock when toggle is on."""
    if _is_mock_request(request):
        result = MockDataGenerator.retry_prediction(features.model_dump())
        return RetryPredictionOut(**{k: v for k, v in result.items() if k != "_source"})
    try:
        result = await service.call_retry_model(features.model_dump())
    except Exception as exc:
        logger.exception("Retry model prediction failed")
        raise HTTPException(status_code=502, detail=f"ML model error: {exc}") from exc
    return RetryPredictionOut(**result)

