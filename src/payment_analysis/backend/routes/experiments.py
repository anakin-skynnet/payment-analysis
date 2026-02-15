"""Experiments API: A/B experiment CRUD, assignment, and results analysis for decisioning."""

from __future__ import annotations

import math
from typing import Any, Optional, cast

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, func
from sqlmodel import select

from ..db_models import DecisionLog, DecisionOutcome, Experiment, ExperimentAssignment, utcnow
from ..dependencies import SessionDep

router = APIRouter(tags=["experiments"])


class ExperimentIn(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None


class AssignIn(BaseModel):
    subject_key: str = Field(min_length=1)
    variant: str = Field(min_length=1)


@router.post("", response_model=Experiment, operation_id="createExperiment")
def create_experiment(payload: ExperimentIn, session: SessionDep) -> Experiment:
    exp = Experiment(name=payload.name, description=payload.description)
    session.add(exp)
    session.commit()
    session.refresh(exp)
    return exp


@router.get("", response_model=list[Experiment], operation_id="listExperiments")
def list_experiments(
    session: SessionDep,
    limit: int = Query(100, ge=1, le=200, description="Max number of experiments"),
) -> list[Experiment]:
    limit = max(1, min(limit, 200))
    stmt = select(Experiment).order_by(desc(cast(Any, Experiment.created_at))).limit(
        limit
    )
    return list(session.exec(stmt).all())


@router.post("/{experiment_id}/start", response_model=Experiment, operation_id="startExperiment")
def start_experiment(experiment_id: str, session: SessionDep) -> Experiment:
    exp = session.get(Experiment, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    exp.status = "running"
    exp.started_at = exp.started_at or utcnow()
    session.add(exp)
    session.commit()
    session.refresh(exp)
    return exp


@router.post("/{experiment_id}/stop", response_model=Experiment, operation_id="stopExperiment")
def stop_experiment(experiment_id: str, session: SessionDep) -> Experiment:
    exp = session.get(Experiment, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    exp.status = "stopped"
    exp.ended_at = utcnow()
    session.add(exp)
    session.commit()
    session.refresh(exp)
    return exp


@router.post(
    "/{experiment_id}/assign",
    response_model=ExperimentAssignment,
    operation_id="assignExperiment",
)
def assign(experiment_id: str, payload: AssignIn, session: SessionDep) -> ExperimentAssignment:
    exp = session.get(Experiment, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if exp.status not in {"running", "draft"}:
        raise HTTPException(status_code=400, detail="Experiment is not assignable")

    assignment = ExperimentAssignment(
        experiment_id=experiment_id,
        subject_key=payload.subject_key,
        variant=payload.variant,
    )
    session.add(assignment)
    session.commit()
    session.refresh(assignment)
    return assignment


@router.get(
    "/{experiment_id}/assignments",
    response_model=list[ExperimentAssignment],
    operation_id="listExperimentAssignments",
)
def list_assignments(
    experiment_id: str, session: SessionDep, limit: int = 200
) -> list[ExperimentAssignment]:
    limit = max(1, min(limit, 500))
    stmt = (
        select(ExperimentAssignment)
        .where(ExperimentAssignment.experiment_id == experiment_id)
        .order_by(desc(cast(Any, ExperimentAssignment.created_at)))
        .limit(limit)
    )
    return list(session.exec(stmt).all())


class VariantStats(BaseModel):
    variant: str
    subjects: int
    decisions: int
    outcomes: int
    approval_rate: Optional[float] = None
    avg_latency_ms: Optional[float] = None


class ExperimentResultsOut(BaseModel):
    """A/B experiment results with lift and statistical significance."""
    experiment_id: str
    experiment_name: str
    status: str
    control: Optional[VariantStats] = None
    treatment: Optional[VariantStats] = None
    lift_pct: Optional[float] = None      # (treatment - control) / control * 100
    p_value: Optional[float] = None       # two-proportion z-test p-value
    is_significant: bool = False           # p_value < 0.05
    recommendation: str = "Not enough data to recommend."


@router.get(
    "/{experiment_id}/results",
    response_model=ExperimentResultsOut,
    operation_id="getExperimentResults",
)
def get_experiment_results(experiment_id: str, session: SessionDep) -> ExperimentResultsOut:
    """Compute A/B experiment results: lift, p-value, and recommendation.

    Joins experiment assignments → decision logs → decision outcomes to compute
    per-variant approval rates and statistical significance via a two-proportion z-test.
    """
    exp = session.get(Experiment, experiment_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Get assignments per variant
    assignments = session.exec(
        select(ExperimentAssignment)
        .where(ExperimentAssignment.experiment_id == experiment_id)
    ).all()

    variant_subjects: dict[str, set[str]] = {"control": set(), "treatment": set()}
    for a in assignments:
        if a.variant in variant_subjects:
            variant_subjects[a.variant].add(a.subject_key)

    # Get decision logs for these subjects
    all_subject_keys = variant_subjects["control"] | variant_subjects["treatment"]
    if not all_subject_keys:
        return ExperimentResultsOut(
            experiment_id=experiment_id,
            experiment_name=exp.name,
            status=exp.status,
        )

    # Query decision outcomes joined to logs
    variant_stats: dict[str, dict[str, Any]] = {}
    for variant_name, subjects in variant_subjects.items():
        if not subjects:
            continue
        # Count outcomes by looking at decision logs with matching experiment_id
        decisions = session.exec(
            select(DecisionLog)
            .where(cast(Any, DecisionLog.response)["experiment_id"].as_string() == experiment_id)
            .where(cast(Any, DecisionLog.response)["variant"].as_string() == variant_name)
        ).all()

        outcomes = session.exec(
            select(DecisionOutcome)
            .where(DecisionOutcome.audit_id.in_([d.audit_id for d in decisions]))  # type: ignore[union-attr]
        ).all() if decisions else []

        approved = sum(1 for o in outcomes if o.outcome == "approved")
        total_outcomes = len(outcomes)

        variant_stats[variant_name] = {
            "subjects": len(subjects),
            "decisions": len(decisions),
            "outcomes": total_outcomes,
            "approved": approved,
            "approval_rate": (approved / total_outcomes) if total_outcomes > 0 else None,
            "avg_latency_ms": (
                sum(o.latency_ms for o in outcomes if o.latency_ms) / len([o for o in outcomes if o.latency_ms])
                if any(o.latency_ms for o in outcomes) else None
            ),
        }

    control = variant_stats.get("control")
    treatment = variant_stats.get("treatment")

    control_out = VariantStats(
        variant="control",
        subjects=control["subjects"] if control else 0,
        decisions=control["decisions"] if control else 0,
        outcomes=control["outcomes"] if control else 0,
        approval_rate=control["approval_rate"] if control else None,
        avg_latency_ms=control["avg_latency_ms"] if control else None,
    ) if control else None

    treatment_out = VariantStats(
        variant="treatment",
        subjects=treatment["subjects"] if treatment else 0,
        decisions=treatment["decisions"] if treatment else 0,
        outcomes=treatment["outcomes"] if treatment else 0,
        approval_rate=treatment["approval_rate"] if treatment else None,
        avg_latency_ms=treatment["avg_latency_ms"] if treatment else None,
    ) if treatment else None

    # Compute lift and p-value
    lift_pct: float | None = None
    p_value: float | None = None
    is_significant = False
    recommendation = "Not enough data to recommend."

    if (control and treatment
            and control["outcomes"] > 0 and treatment["outcomes"] > 0
            and control["approval_rate"] is not None and treatment["approval_rate"] is not None):

        c_rate = control["approval_rate"]
        t_rate = treatment["approval_rate"]
        c_n = control["outcomes"]
        t_n = treatment["outcomes"]

        if c_rate > 0:
            lift_pct = ((t_rate - c_rate) / c_rate) * 100

        # Two-proportion z-test
        pooled = (control["approved"] + treatment["approved"]) / (c_n + t_n)
        if pooled > 0 and pooled < 1:
            se = math.sqrt(pooled * (1 - pooled) * (1 / c_n + 1 / t_n))
            if se > 0:
                z = (t_rate - c_rate) / se
                # Approximate p-value using normal CDF
                p_value = 2 * (1 - _normal_cdf(abs(z)))
                is_significant = p_value < 0.05

        if is_significant:
            if lift_pct is not None and lift_pct > 0:
                recommendation = f"Treatment shows +{lift_pct:.1f}% lift (p={p_value:.4f}). Recommend graduating treatment to production."
            elif lift_pct is not None and lift_pct < 0:
                recommendation = f"Treatment shows {lift_pct:.1f}% decline (p={p_value:.4f}). Recommend stopping experiment and keeping control."
            else:
                recommendation = f"No meaningful difference (p={p_value:.4f}). Consider extending the experiment."
        else:
            min_samples = max(100, c_n + t_n)
            recommendation = f"Not yet significant (p={p_value:.4f if p_value else 'N/A'}). Need ~{min_samples * 2} total outcomes for reliable results."

    return ExperimentResultsOut(
        experiment_id=experiment_id,
        experiment_name=exp.name,
        status=exp.status,
        control=control_out,
        treatment=treatment_out,
        lift_pct=lift_pct,
        p_value=p_value,
        is_significant=is_significant,
        recommendation=recommendation,
    )


def _normal_cdf(x: float) -> float:
    """Approximate the standard normal CDF using the error function."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

