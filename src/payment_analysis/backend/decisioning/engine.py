"""DecisionEngine: data-driven decisioning with Lakebase config, rule evaluation, and ML enrichment.

Responsibilities:
1. Load and cache ``DecisionConfig`` (tunable thresholds) from Lakebase (TTL ~60 s).
2. Load and cache ``RetryableDeclineCode`` from Lakebase.
3. Load and cache ``RoutePerformance`` from Lakebase.
4. Fetch active ``approval_rules`` and evaluate them against the DecisionContext.
5. Call ML Model Serving endpoints to enrich context with live scores (risk, approval, retry, routing).
6. Delegate to policy functions in ``policies.py`` with loaded parameters.
7. Record decision outcomes for the learning loop.

The engine is instantiated per-request (lightweight) but the caches are module-level singletons
refreshed on a TTL so repeated requests within a window don't hit the database.
"""

from __future__ import annotations

import asyncio
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from .rule_engine import evaluate_condition
from .schemas import (
    AuthDecisionOut,
    DecisionContext,
    RetryDecisionOut,
    RoutingDecisionOut,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cache layer (module-level singletons)
# ---------------------------------------------------------------------------

_CACHE_TTL_SECONDS = 60  # Refresh config every 60 s


@dataclass
class _CacheEntry:
    data: Any = None
    fetched_at: float = 0.0

    @property
    def is_stale(self) -> bool:
        return (time.monotonic() - self.fetched_at) > _CACHE_TTL_SECONDS


_config_cache = _CacheEntry()
_decline_codes_cache = _CacheEntry()
_routes_cache = _CacheEntry()
_rules_cache = _CacheEntry()
_recommendations_cache = _CacheEntry()

# P3 #20: Cache lock to prevent race conditions on concurrent requests
_cache_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Decision parameters (loaded from Lakebase, with sensible defaults)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DecisionParams:
    """All tunable decision parameters. Loaded from DecisionConfig table."""

    risk_threshold_high: float = 0.75
    risk_threshold_medium: float = 0.35
    device_trust_low_risk: float = 0.90
    retry_max_attempts_control: int = 3
    retry_max_attempts_treatment: int = 4
    retry_backoff_recurring_control: int = 900
    retry_backoff_recurring_treatment: int = 300
    retry_backoff_transient: int = 60
    retry_backoff_soft_treatment: int = 1800
    routing_domestic_country: str = "BR"
    ml_enrichment_enabled: bool = True
    ml_enrichment_timeout_ms: int = 2000
    rule_engine_enabled: bool = True


def _params_from_config(rows: list[dict[str, str]]) -> DecisionParams:
    """Build DecisionParams from key-value rows (from DecisionConfig table)."""
    kv: dict[str, str] = {}
    for row in rows:
        k = str(row.get("key", "")).strip()
        v = str(row.get("value", "")).strip()
        if k and v:
            kv[k] = v

    def _float(key: str, default: float) -> float:
        try:
            return float(kv.get(key, default))
        except (ValueError, TypeError):
            return default

    def _int(key: str, default: int) -> int:
        try:
            return int(float(kv.get(key, default)))
        except (ValueError, TypeError):
            return default

    def _bool(key: str, default: bool) -> bool:
        v = kv.get(key, str(default)).lower()
        return v in ("true", "1", "yes")

    return DecisionParams(
        risk_threshold_high=_float("risk_threshold_high", 0.75),
        risk_threshold_medium=_float("risk_threshold_medium", 0.35),
        device_trust_low_risk=_float("device_trust_low_risk", 0.90),
        retry_max_attempts_control=_int("retry_max_attempts_control", 3),
        retry_max_attempts_treatment=_int("retry_max_attempts_treatment", 4),
        retry_backoff_recurring_control=_int("retry_backoff_recurring_control", 900),
        retry_backoff_recurring_treatment=_int("retry_backoff_recurring_treatment", 300),
        retry_backoff_transient=_int("retry_backoff_transient", 60),
        retry_backoff_soft_treatment=_int("retry_backoff_soft_treatment", 1800),
        routing_domestic_country=kv.get("routing_domestic_country", "BR"),
        ml_enrichment_enabled=_bool("ml_enrichment_enabled", True),
        ml_enrichment_timeout_ms=_int("ml_enrichment_timeout_ms", 2000),
        rule_engine_enabled=_bool("rule_engine_enabled", True),
    )


# ---------------------------------------------------------------------------
# Decline code helpers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RetryableCode:
    code: str
    category: str
    default_backoff_seconds: int
    max_attempts: int


def _decline_codes_map(rows: list[dict[str, Any]]) -> dict[str, RetryableCode]:
    """Build a lookup from code → RetryableCode."""
    result: dict[str, RetryableCode] = {}
    for row in rows:
        code = str(row.get("code", "")).strip().lower()
        if not code:
            continue
        result[code] = RetryableCode(
            code=code,
            category=str(row.get("category", "soft")),
            default_backoff_seconds=int(row.get("default_backoff_seconds", 900)),
            max_attempts=int(row.get("max_attempts", 3)),
        )
    return result


# ---------------------------------------------------------------------------
# Route performance helpers
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RouteScore:
    route_name: str
    approval_rate_pct: float
    avg_latency_ms: float
    cost_score: float


def _route_scores_list(rows: list[dict[str, Any]]) -> list[RouteScore]:
    """Build ordered list of RouteScore from RoutePerformance rows."""
    result: list[RouteScore] = []
    for row in rows:
        result.append(RouteScore(
            route_name=str(row.get("route_name", "")),
            approval_rate_pct=float(row.get("approval_rate_pct", 50.0)),
            avg_latency_ms=float(row.get("avg_latency_ms", 500.0)),
            cost_score=float(row.get("cost_score", 0.5)),
        ))
    # Sort by composite score: higher approval rate, lower latency, lower cost → better
    result.sort(
        key=lambda r: (-r.approval_rate_pct, r.avg_latency_ms, r.cost_score)
    )
    return result


# ---------------------------------------------------------------------------
# DecisionEngine
# ---------------------------------------------------------------------------

class DecisionEngine:
    """Data-driven decision engine backed by Lakebase config, rules, and ML models."""

    def __init__(
        self,
        session: Any | None = None,
        service: Any | None = None,
        runtime: Any | None = None,
    ) -> None:
        self._session = session
        self._service = service  # DatabricksService for ML calls
        self._runtime = runtime

    # -- Cache loaders -------------------------------------------------------

    def _load_config(self) -> DecisionParams:
        """Load DecisionConfig from Lakebase (cached, thread-safe)."""
        global _config_cache
        if not _config_cache.is_stale and _config_cache.data is not None:
            return _config_cache.data

        with _cache_lock:
            # Double-check after acquiring lock
            if not _config_cache.is_stale and _config_cache.data is not None:
                return _config_cache.data

            rows: list[dict[str, str]] = []
            if self._runtime:
                try:
                    rows = self._read_decision_config_from_lakebase()
                except Exception as e:
                    logger.debug("Could not load decision_config from Lakebase: %s", e)

            params = _params_from_config(rows) if rows else DecisionParams()
            _config_cache.data = params
            _config_cache.fetched_at = time.monotonic()
            return params

    def _load_decline_codes(self) -> dict[str, RetryableCode]:
        """Load RetryableDeclineCode from Lakebase (cached)."""
        global _decline_codes_cache
        if not _decline_codes_cache.is_stale and _decline_codes_cache.data is not None:
            return _decline_codes_cache.data

        rows: list[dict[str, Any]] = []
        if self._runtime:
            try:
                rows = self._read_decline_codes_from_lakebase()
            except Exception as e:
                logger.debug("Could not load retryable decline codes from Lakebase: %s", e)

        codes = _decline_codes_map(rows) if rows else {}
        _decline_codes_cache.data = codes
        _decline_codes_cache.fetched_at = time.monotonic()
        return codes

    def _load_routes(self) -> list[RouteScore]:
        """Load RoutePerformance from Lakebase (cached)."""
        global _routes_cache
        if not _routes_cache.is_stale and _routes_cache.data is not None:
            return _routes_cache.data

        rows: list[dict[str, Any]] = []
        if self._runtime:
            try:
                rows = self._read_route_performance_from_lakebase()
            except Exception as e:
                logger.debug("Could not load route performance from Lakebase: %s", e)

        routes = _route_scores_list(rows) if rows else []
        _routes_cache.data = routes
        _routes_cache.fetched_at = time.monotonic()
        return routes

    def _load_rules(self, rule_type: str | None = None) -> list[dict[str, Any]]:
        """Load active approval_rules from Lakebase (cached, filtered by rule_type)."""
        global _rules_cache
        if not _rules_cache.is_stale and _rules_cache.data is not None:
            all_rules: list[dict[str, Any]] = _rules_cache.data
        else:
            all_rules = []
            if self._runtime:
                try:
                    from ..lakebase_config import get_approval_rules_from_lakebase
                    result = get_approval_rules_from_lakebase(
                        self._runtime, active_only=True, limit=200
                    )
                    if result is not None:
                        all_rules = result
                except Exception as e:
                    logger.debug("Could not load approval rules from Lakebase: %s", e)
            _rules_cache.data = all_rules
            _rules_cache.fetched_at = time.monotonic()

        if rule_type:
            return [r for r in all_rules if r.get("rule_type") == rule_type]
        return all_rules

    def _load_recommendations(self, decision_type: str | None = None) -> list[dict[str, Any]]:
        """Load recent agent recommendations from Lakebase approval_recommendations (cached).

        This closes the recommendation-to-decision loop: agents propose actions,
        the engine consumes them to influence live decisions.
        """
        global _recommendations_cache
        if not _recommendations_cache.is_stale and _recommendations_cache.data is not None:
            all_recs: list[dict[str, Any]] = _recommendations_cache.data
        else:
            all_recs = []
            if self._runtime:
                try:
                    all_recs = self._read_recommendations_from_lakebase()
                except Exception as e:
                    logger.debug("Could not load recommendations from Lakebase: %s", e)
            _recommendations_cache.data = all_recs
            _recommendations_cache.fetched_at = time.monotonic()

        if decision_type:
            return [r for r in all_recs if r.get("recommendation_type") == decision_type]
        return all_recs

    def _read_recommendations_from_lakebase(self) -> list[dict[str, Any]]:
        """Read recent agent recommendations (last 24h) from Lakebase."""
        if not self._runtime:
            return []
        from sqlalchemy import text as sa_text

        schema = self._get_schema_name()
        with self._runtime.get_session() as session:
            q = sa_text(
                f'SELECT id, recommendation_type, segment, action_summary, expected_impact_pct, '
                f'confidence, status, created_at '
                f'FROM "{schema}".approval_recommendations '
                f"WHERE status = 'active' AND created_at >= NOW() - INTERVAL '24 hours' "
                f'ORDER BY confidence DESC LIMIT 50'
            )
            try:
                result = session.execute(q)
                return [
                    {
                        "id": str(r[0]),
                        "recommendation_type": str(r[1]),
                        "segment": str(r[2]) if r[2] else None,
                        "action_summary": str(r[3]),
                        "expected_impact_pct": float(r[4]) if r[4] else 0.0,
                        "confidence": float(r[5]) if r[5] else 0.0,
                        "status": str(r[6]),
                    }
                    for r in result.fetchall()
                ]
            except Exception:
                return []

    async def _lookup_similar_transactions(
        self, ctx: DecisionContext, params: DecisionParams
    ) -> dict[str, Any]:
        """Look up similar historical transactions via Vector Search for decision context.

        Returns aggregated stats from similar transactions (approval rate, common routes,
        risk distribution) that inform the decision. Falls back gracefully if unavailable.
        """
        if not self._service or not self._service.is_available:
            return {}
        try:
            description = (
                f"Payment of {ctx.amount_minor / 100:.2f} from {ctx.issuer_country or 'unknown'} "
                f"merchant {ctx.merchant_id} network {ctx.network or 'unknown'} "
                f"risk {ctx.risk_score or 0:.2f}"
            )
            timeout = params.ml_enrichment_timeout_ms / 1000.0
            similar = await asyncio.wait_for(
                self._service.vector_search_similar(description, num_results=5),
                timeout=timeout,
            )
            if similar and isinstance(similar, list) and len(similar) > 0:
                approval_rates = [s.get("approval_rate_pct", 50) for s in similar if s.get("approval_rate_pct") is not None]
                avg_approval = sum(approval_rates) / len(approval_rates) if approval_rates else None
                return {
                    "similar_count": len(similar),
                    "similar_avg_approval_rate": avg_approval,
                    "similar_top_route": similar[0].get("payment_solution", ""),
                    "similar_avg_fraud_score": sum(s.get("avg_fraud_score", 0) for s in similar) / len(similar),
                }
        except Exception as e:
            logger.debug("Vector Search lookup failed (graceful): %s", e)
        return {}

    # -- Lakebase readers (raw SQL via session) -------------------------------

    def _read_decision_config_from_lakebase(self) -> list[dict[str, str]]:
        if not self._runtime:
            return []
        from sqlalchemy import text as sa_text

        schema = self._get_schema_name()
        with self._runtime.get_session() as session:
            q = sa_text(f'SELECT key, value FROM "{schema}".decisionconfig')
            result = session.execute(q)
            return [{"key": str(r[0]), "value": str(r[1])} for r in result.fetchall()]

    def _read_decline_codes_from_lakebase(self) -> list[dict[str, Any]]:
        if not self._runtime:
            return []
        from sqlalchemy import text as sa_text

        schema = self._get_schema_name()
        with self._runtime.get_session() as session:
            q = sa_text(
                f'SELECT code, label, category, default_backoff_seconds, max_attempts '
                f'FROM "{schema}".retryabledeclinecode WHERE is_active = true'
            )
            result = session.execute(q)
            return [
                {
                    "code": str(r[0]),
                    "label": str(r[1]),
                    "category": str(r[2]),
                    "default_backoff_seconds": int(r[3]),
                    "max_attempts": int(r[4]),
                }
                for r in result.fetchall()
            ]

    def _read_route_performance_from_lakebase(self) -> list[dict[str, Any]]:
        if not self._runtime:
            return []
        from sqlalchemy import text as sa_text

        schema = self._get_schema_name()
        with self._runtime.get_session() as session:
            q = sa_text(
                f'SELECT route_name, approval_rate_pct, avg_latency_ms, cost_score '
                f'FROM "{schema}".routeperformance WHERE is_active = true '
                f'ORDER BY approval_rate_pct DESC'
            )
            result = session.execute(q)
            return [
                {
                    "route_name": str(r[0]),
                    "approval_rate_pct": float(r[1]),
                    "avg_latency_ms": float(r[2]),
                    "cost_score": float(r[3]),
                }
                for r in result.fetchall()
            ]

    def _get_schema_name(self) -> str:
        if self._runtime and self._runtime.config:
            return (self._runtime.config.db.db_schema or "payment_analysis").strip() or "payment_analysis"
        return "payment_analysis"

    # -- ML enrichment -------------------------------------------------------

    def _build_ml_features(self, ctx: DecisionContext, params: DecisionParams) -> dict:
        """Build feature dict matching training features exactly (P0 fix: training/inference parity).

        The ML models are trained with: amount, fraud_score, device_trust_score, is_cross_border,
        retry_count, uses_3ds, merchant_segment, card_network, log_amount, hour_of_day, day_of_week,
        is_weekend, network_encoded, risk_amount_interaction. All must be present at inference.
        """
        import math
        from datetime import datetime

        amount = ctx.amount_minor / 100.0
        fraud_score = ctx.risk_score or 0.1
        log_amount = math.log1p(max(0, amount))
        now = datetime.utcnow()
        network_str = (ctx.network or "visa").lower()
        network_map = {"visa": 0, "mastercard": 1, "amex": 2, "elo": 3, "hipercard": 4}

        return {
            "amount": amount,
            "fraud_score": fraud_score,
            "device_trust_score": ctx.device_trust_score or 0.8,
            "is_cross_border": bool(ctx.issuer_country and ctx.issuer_country.upper() != params.routing_domestic_country),
            "retry_count": ctx.attempt_number,
            "uses_3ds": ctx.supports_passkey,
            "merchant_segment": ctx.metadata.get("merchant_segment", "retail"),
            "card_network": network_str,
            # Temporal features (match training)
            "log_amount": log_amount,
            "hour_of_day": now.hour,
            "day_of_week": now.weekday(),
            "is_weekend": int(now.weekday() >= 5),
            # Encoded features
            "network_encoded": network_map.get(network_str, 5),
            "risk_amount_interaction": fraud_score * log_amount,
        }

    async def _enrich_with_ml(
        self, ctx: DecisionContext, params: DecisionParams
    ) -> DecisionContext:
        """Enrich DecisionContext with ML model scores (risk, approval) when available.

        Calls ML serving endpoints in parallel with a timeout (P2 #13: parallelized).
        Feature dict matches training features exactly (P0 #1).
        """
        if not params.ml_enrichment_enabled or not self._service or not self._service.is_available:
            return ctx

        timeout = params.ml_enrichment_timeout_ms / 1000.0
        features = self._build_ml_features(ctx, params)

        enriched = ctx.model_copy()

        async def _call_risk() -> dict | None:
            try:
                return await asyncio.wait_for(self._service.call_risk_model(features), timeout=timeout)
            except Exception as e:
                logger.debug("ML risk enrichment failed (graceful): %s", e)
                return None

        async def _call_approval() -> dict | None:
            try:
                return await asyncio.wait_for(self._service.call_approval_model(features), timeout=timeout)
            except Exception as e:
                logger.debug("ML approval enrichment failed (graceful): %s", e)
                return None

        risk_result, approval_result = await asyncio.gather(_call_risk(), _call_approval())

        if risk_result:
            ml_risk = risk_result.get("risk_score")
            if ml_risk is not None and enriched.risk_score is None:
                enriched.risk_score = float(ml_risk)
            enriched.metadata = {**enriched.metadata, "ml_risk_score": float(ml_risk) if ml_risk else None, "ml_risk_tier": risk_result.get("risk_tier", "")}

        if approval_result:
            approval_prob = approval_result.get("approval_probability")
            if approval_prob is not None:
                enriched.metadata = {**enriched.metadata, "ml_approval_probability": float(approval_prob), "ml_model_version": approval_result.get("model_version", "")}

        return enriched

    # -- Rule evaluation -----------------------------------------------------

    def _evaluate_rules(
        self, ctx_dict: dict[str, Any], rule_type: str
    ) -> list[dict[str, Any]]:
        """Evaluate active rules of the given type against the context.

        Returns list of matching rules (sorted by priority).
        """
        rules = self._load_rules(rule_type=rule_type)
        matching: list[dict[str, Any]] = []
        for rule in rules:
            expr = rule.get("condition_expression")
            try:
                if evaluate_condition(ctx_dict, expr):
                    matching.append(rule)
            except Exception as e:
                logger.debug("Rule evaluation failed for %s: %s", rule.get("id"), e)
        return matching

    # -- Decision methods (data-driven) --------------------------------------

    async def decide_authentication(
        self, ctx: DecisionContext, variant: str | None = None
    ) -> AuthDecisionOut:
        """Data-driven authentication decision: VS + ML (parallel) → recommendations → rule evaluation → policy."""
        from .policies import decide_authentication as _policy_auth, serialize_context

        params = self._load_config()

        # P2 #13: Run Vector Search and ML enrichment in parallel
        vs_task = self._lookup_similar_transactions(ctx, params)
        ml_task = self._enrich_with_ml(ctx, params)
        vs_context, enriched = await asyncio.gather(vs_task, ml_task)

        if vs_context:
            enriched = enriched.model_copy()
            enriched.metadata = {**enriched.metadata, **{f"vs_{k}": v for k, v in vs_context.items()}}

        # Agent recommendation enrichment (closes the recommendation loop)
        recs = self._load_recommendations("authentication")
        if recs:
            top_rec = recs[0]
            enriched = enriched.model_copy()
            enriched.metadata = {
                **enriched.metadata,
                "agent_recommendation": top_rec["action_summary"],
                "agent_confidence": top_rec["confidence"],
                "agent_expected_impact": top_rec["expected_impact_pct"],
            }

        # P1 #4: Enrich with streaming real-time features (approval_rate_5m, etc.)
        streaming = self._read_streaming_features(enriched)
        if streaming:
            enriched = enriched.model_copy()
            enriched.metadata = {**enriched.metadata, **{f"stream_{k}": v for k, v in streaming.items()}}

        # Run policy with data-driven parameters
        decision = _policy_auth(enriched, variant=variant, params=params)

        # Write ML features to online_features table (populates the previously empty table)
        ml_features = {k: v for k, v in enriched.metadata.items() if k.startswith("ml_")}
        if ml_features:
            self._write_online_features(
                entity_id=f"auth_{decision.audit_id}",
                features=ml_features,
            )

        # Rule evaluation: check if any active authentication rules override
        if params.rule_engine_enabled:
            ctx_dict = serialize_context(enriched)
            matching = self._evaluate_rules(ctx_dict, "authentication")
            if matching:
                top_rule = matching[0]
                decision.reason = f"[Rule: {top_rule['name']}] {top_rule['action_summary']}"
                decision.metadata = {  # type: ignore[attr-defined]
                    **(getattr(decision, "metadata", None) or {}),
                    "matched_rule_id": top_rule["id"],
                    "matched_rule_name": top_rule["name"],
                }

        return decision

    async def decide_retry(
        self, ctx: DecisionContext, variant: str | None = None
    ) -> RetryDecisionOut:
        """Data-driven retry decision: VS + retry ML (parallel) → recommendations → Lakebase codes → policy."""
        from .policies import decide_retry as _policy_retry

        params = self._load_config()
        decline_codes = self._load_decline_codes()

        # P2 #13: Run VS and retry ML in parallel
        async def _retry_ml() -> dict | None:
            if not params.ml_enrichment_enabled or not self._service or not self._service.is_available:
                return None
            try:
                features = self._build_ml_features(ctx, params)
                timeout = params.ml_enrichment_timeout_ms / 1000.0
                return await asyncio.wait_for(self._service.call_retry_model(features), timeout=timeout)
            except Exception as e:
                logger.debug("ML retry enrichment failed (graceful): %s", e)
                return None

        vs_context, retry_result = await asyncio.gather(
            self._lookup_similar_transactions(ctx, params), _retry_ml()
        )

        enriched = ctx.model_copy() if vs_context else ctx
        if vs_context:
            enriched.metadata = {**enriched.metadata, **{f"vs_{k}": v for k, v in vs_context.items()}}

        # Agent recommendation enrichment
        recs = self._load_recommendations("retry")
        if recs:
            enriched = enriched.model_copy()
            enriched.metadata = {
                **enriched.metadata,
                "agent_recommendation": recs[0]["action_summary"],
                "agent_confidence": recs[0]["confidence"],
            }

        # ML retry enrichment
        if retry_result:
            retry_prob = retry_result.get("retry_success_probability")
            if retry_prob is not None:
                enriched = enriched.model_copy()
                retry_meta: dict[str, Any] = {
                    **enriched.metadata,
                    "ml_retry_probability": float(retry_prob),
                    "ml_should_retry": retry_result.get("should_retry", False),
                    "ml_model_version": retry_result.get("model_version", ""),
                }
                ml_delay = retry_result.get("retry_delay_seconds") or retry_result.get("suggested_delay_s")
                if ml_delay is not None:
                    retry_meta["ml_retry_delay_seconds"] = float(ml_delay)
                enriched.metadata = retry_meta

        decision = _policy_retry(enriched, variant=variant, params=params, decline_codes=decline_codes)

        # Write ML features to online_features
        ml_features = {k: v for k, v in enriched.metadata.items() if k.startswith("ml_")}
        if ml_features:
            self._write_online_features(
                entity_id=f"retry_{decision.audit_id}",
                features=ml_features,
            )

        # Rule evaluation for retry rules
        if params.rule_engine_enabled:
            from .policies import serialize_context
            ctx_dict = serialize_context(enriched)
            matching = self._evaluate_rules(ctx_dict, "retry")
            if matching:
                top_rule = matching[0]
                decision.reason = f"[Rule: {top_rule['name']}] {top_rule['action_summary']}"

        return decision

    async def decide_routing(
        self, ctx: DecisionContext, variant: str | None = None
    ) -> RoutingDecisionOut:
        """Data-driven routing decision: VS + routing ML (parallel) → recommendations → Lakebase routes → policy."""
        from .policies import decide_routing as _policy_routing

        params = self._load_config()
        route_scores = self._load_routes()

        # P2 #13: Run VS and routing ML in parallel
        async def _routing_ml() -> dict | None:
            if not params.ml_enrichment_enabled or not self._service or not self._service.is_available:
                return None
            try:
                features = self._build_ml_features(ctx, params)
                timeout = params.ml_enrichment_timeout_ms / 1000.0
                return await asyncio.wait_for(self._service.call_routing_model(features), timeout=timeout)
            except Exception as e:
                logger.debug("ML routing enrichment failed (graceful): %s", e)
                return None

        vs_context, routing_result = await asyncio.gather(
            self._lookup_similar_transactions(ctx, params), _routing_ml()
        )

        enriched = ctx.model_copy() if vs_context else ctx
        if vs_context:
            enriched.metadata = {**enriched.metadata, **{f"vs_{k}": v for k, v in vs_context.items()}}

        # Agent recommendation enrichment
        recs = self._load_recommendations("routing")
        if recs:
            enriched = enriched.model_copy()
            enriched.metadata = {
                **enriched.metadata,
                "agent_recommendation": recs[0]["action_summary"],
                "agent_confidence": recs[0]["confidence"],
            }

        # ML routing enrichment
        if routing_result:
            ml_route = routing_result.get("recommended_solution")
            if ml_route:
                enriched = enriched.model_copy()
                enriched.metadata = {
                    **enriched.metadata,
                    "ml_recommended_route": ml_route,
                    "ml_route_confidence": routing_result.get("confidence", 0.0),
                    "ml_route_alternatives": routing_result.get("alternatives", []),
                }

        decision = _policy_routing(
            enriched, variant=variant, params=params, route_scores=route_scores
        )

        # Write ML features to online_features
        ml_features = {k: v for k, v in enriched.metadata.items() if k.startswith("ml_")}
        if ml_features:
            self._write_online_features(
                entity_id=f"routing_{decision.audit_id}",
                features=ml_features,
            )

        # Rule evaluation for routing rules
        if params.rule_engine_enabled:
            from .policies import serialize_context
            ctx_dict = serialize_context(enriched)
            matching = self._evaluate_rules(ctx_dict, "routing")
            if matching:
                top_rule = matching[0]
                decision.reason = f"[Rule: {top_rule['name']}] {top_rule['action_summary']}"

        return decision

    # -- P1 #4: Streaming features reader ------------------------------------

    def _read_streaming_features(self, ctx: DecisionContext) -> dict[str, Any]:
        """Read real-time behavioral features from online_features_stream (computed by continuous_processor).

        These include approval_rate_5m, retry_rate_5m, avg_fraud_5m for the card/merchant.
        """
        if not self._runtime or not self._runtime._db_configured():
            return {}
        try:
            from sqlalchemy import text as sa_text
            schema = self._get_schema_name()
            merchant = ctx.merchant_id
            with self._runtime.get_session() as session:
                q = sa_text(
                    f'SELECT feature_name, feature_value FROM "{schema}".online_features '
                    f"WHERE entity_id = :entity_id AND source = 'streaming' "
                    f"ORDER BY id DESC LIMIT 10"
                )
                result = session.execute(q, {"entity_id": merchant})
                features = {}
                for row in result.fetchall():
                    features[str(row[0])] = float(row[1]) if row[1] is not None else None
                return features
        except Exception as e:
            logger.debug("Could not read streaming features: %s", e)
            return {}

    # -- Online features writer -----------------------------------------------

    def _write_online_features(
        self, entity_id: str, features: dict[str, Any], source: str = "ml"
    ) -> None:
        """Write ML enrichment scores to Lakebase online_features table.

        This populates the previously-empty online_features table so the
        Online Features API (GET /api/analytics/online-features) returns
        real data from the decision flow instead of mock data.
        """
        if not self._runtime or not self._runtime._db_configured():
            return

        try:
            from sqlalchemy import text as sa_text
            import uuid

            schema = self._get_schema_name()
            with self._runtime.get_session() as session:
                for feature_name, value in features.items():
                    if value is None:
                        continue
                    fid = uuid.uuid4().hex[:16]
                    is_numeric = isinstance(value, (int, float))
                    q = sa_text(
                        f'INSERT INTO "{schema}".online_features '
                        f"(id, source, feature_set, feature_name, feature_value, feature_value_str, entity_id) "
                        f"VALUES (:id, :source, :feature_set, :feature_name, :feature_value, :feature_value_str, :entity_id)"
                    )
                    session.execute(q, {
                        "id": fid,
                        "source": source,
                        "feature_set": "decision_enrichment",
                        "feature_name": feature_name,
                        "feature_value": float(value) if is_numeric else None,
                        "feature_value_str": None if is_numeric else str(value),
                        "entity_id": entity_id,
                    })
                session.commit()
        except Exception as e:
            logger.debug("Failed to write online features: %s", e)

    # -- Outcome recording ---------------------------------------------------

    def record_outcome(
        self,
        audit_id: str,
        decision_type: str,
        outcome: str,
        outcome_code: str | None = None,
        outcome_reason: str | None = None,
        latency_ms: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Record a decision outcome in Lakebase for the learning loop."""
        if not self._session:
            return False
        try:
            from ..db_models import DecisionOutcome

            self._session.add(
                DecisionOutcome(
                    audit_id=audit_id,
                    decision_type=decision_type,
                    outcome=outcome,
                    outcome_code=outcome_code,
                    outcome_reason=outcome_reason,
                    latency_ms=latency_ms,
                    extra=metadata or {},
                )
            )
            self._session.commit()
            return True
        except Exception as e:
            logger.warning("Failed to record decision outcome: %s", e)
            return False
