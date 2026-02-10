-- =============================================================================
-- Unity Catalog functions for Databricks Agent Framework (code-based)
-- =============================================================================
-- Run with catalog/schema substituted (e.g. ahs_demos_catalog, payment_analysis).
-- Creates functions in DATA_CATALOG.DATA_SCHEMA (same schema as data). Used by LangGraph via UCFunctionToolkit.
-- Requires: gold views and payments_enriched_silver in DATA_CATALOG.DATA_SCHEMA.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Decline Analyst tools
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION __CATALOG__.__SCHEMA__.get_decline_trends()
RETURNS TABLE(
  decline_reason STRING,
  decline_count BIGINT,
  pct_of_declines DOUBLE,
  avg_fraud_score DOUBLE,
  total_declined_value DOUBLE
)
LANGUAGE SQL
COMMENT 'Get top decline reasons and their characteristics for decline analysis.'
RETURN
  SELECT
    decline_reason,
    decline_count,
    pct_of_declines,
    avg_fraud_score,
    total_declined_value
  FROM __CATALOG__.__SCHEMA__.v_top_decline_reasons
  ORDER BY decline_count DESC
  LIMIT 10;

CREATE OR REPLACE FUNCTION __CATALOG__.__SCHEMA__.get_decline_by_segment()
RETURNS TABLE(
  merchant_segment STRING,
  decline_reason STRING,
  decline_count BIGINT,
  declined_value DOUBLE,
  avg_fraud_score DOUBLE
)
LANGUAGE SQL
COMMENT 'Get decline breakdown by merchant segment.'
RETURN
  SELECT
    merchant_segment,
    decline_reason,
    COUNT(*) AS decline_count,
    ROUND(SUM(amount), 2) AS declined_value,
    ROUND(AVG(fraud_score), 3) AS avg_fraud_score
  FROM __CATALOG__.__SCHEMA__.payments_enriched_silver
  WHERE NOT is_approved
    AND event_date >= CURRENT_DATE - 30
  GROUP BY merchant_segment, decline_reason
  ORDER BY decline_count DESC
  LIMIT 20;

-- -----------------------------------------------------------------------------
-- Smart Routing tools
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION __CATALOG__.__SCHEMA__.get_route_performance()
RETURNS TABLE(
  payment_solution STRING,
  card_network STRING,
  volume BIGINT,
  approval_rate DOUBLE,
  avg_latency DOUBLE
)
LANGUAGE SQL
COMMENT 'Get approval rates and latency by payment route.'
RETURN
  SELECT
    payment_solution,
    card_network,
    COUNT(*) AS volume,
    ROUND(AVG(CASE WHEN is_approved THEN 1.0 ELSE 0.0 END) * 100, 2) AS approval_rate,
    ROUND(AVG(processing_time_ms), 2) AS avg_latency
  FROM __CATALOG__.__SCHEMA__.payments_enriched_silver
  WHERE event_date >= CURRENT_DATE - 7
  GROUP BY payment_solution, card_network
  ORDER BY volume DESC;

CREATE OR REPLACE FUNCTION __CATALOG__.__SCHEMA__.get_cascade_recommendations(merchant_segment STRING)
RETURNS TABLE(
  payment_solution STRING,
  approval_rate DOUBLE,
  latency DOUBLE,
  volume BIGINT
)
LANGUAGE SQL
COMMENT 'Get recommended cascade configuration for a merchant segment.'
RETURN
  SELECT
    payment_solution,
    ROUND(AVG(CASE WHEN is_approved THEN 1.0 ELSE 0.0 END) * 100, 2) AS approval_rate,
    ROUND(AVG(processing_time_ms), 2) AS latency,
    COUNT(*) AS volume
  FROM __CATALOG__.__SCHEMA__.payments_enriched_silver
  WHERE merchant_segment = get_cascade_recommendations.merchant_segment
    AND event_date >= CURRENT_DATE - 30
  GROUP BY payment_solution
  ORDER BY approval_rate DESC
  LIMIT 3;

-- -----------------------------------------------------------------------------
-- Smart Retry tools
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION __CATALOG__.__SCHEMA__.get_retry_success_rates()
RETURNS TABLE(
  decline_reason STRING,
  retry_count INT,
  attempts BIGINT,
  success_rate DOUBLE,
  avg_amount DOUBLE
)
LANGUAGE SQL
COMMENT 'Get historical retry success rates by decline reason.'
RETURN
  SELECT
    decline_reason,
    retry_count,
    COUNT(*) AS attempts,
    ROUND(AVG(CASE WHEN is_approved THEN 1.0 ELSE 0.0 END) * 100, 2) AS success_rate,
    ROUND(AVG(amount), 2) AS avg_amount
  FROM __CATALOG__.__SCHEMA__.payments_enriched_silver
  WHERE is_retry = true
    AND event_date >= CURRENT_DATE - 30
  GROUP BY decline_reason, retry_count
  ORDER BY decline_reason, retry_count;

CREATE OR REPLACE FUNCTION __CATALOG__.__SCHEMA__.get_recovery_opportunities(min_amount DOUBLE)
RETURNS TABLE(
  decline_reason STRING,
  decline_count BIGINT,
  total_value DOUBLE,
  avg_fraud_score DOUBLE,
  recovery_likelihood STRING
)
LANGUAGE SQL
COMMENT 'Find high-value recovery opportunities for retry.'
RETURN
  SELECT
    decline_reason,
    COUNT(*) AS decline_count,
    ROUND(SUM(amount), 2) AS total_value,
    ROUND(AVG(fraud_score), 3) AS avg_fraud_score,
    CASE
      WHEN AVG(fraud_score) < 0.3 THEN 'HIGH'
      WHEN AVG(fraud_score) < 0.5 THEN 'MEDIUM'
      ELSE 'LOW'
    END AS recovery_likelihood
  FROM __CATALOG__.__SCHEMA__.payments_enriched_silver
  WHERE NOT is_approved
    AND amount >= COALESCE(get_recovery_opportunities.min_amount, 100)
    AND fraud_score < 0.5
    AND retry_count < 3
    AND event_date >= CURRENT_DATE - 7
  GROUP BY decline_reason
  HAVING COUNT(*) > 10
  ORDER BY total_value DESC;

-- -----------------------------------------------------------------------------
-- Risk Assessor tools
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION __CATALOG__.__SCHEMA__.get_high_risk_transactions(threshold DOUBLE)
RETURNS TABLE(
  transaction_id STRING,
  merchant_segment STRING,
  amount DOUBLE,
  fraud_score DOUBLE,
  aml_risk_score DOUBLE,
  device_trust_score DOUBLE,
  is_approved BOOLEAN,
  decline_reason STRING
)
LANGUAGE SQL
COMMENT 'Get high-risk transactions requiring review.'
RETURN
  SELECT
    transaction_id,
    merchant_segment,
    amount,
    fraud_score,
    aml_risk_score,
    device_trust_score,
    is_approved,
    decline_reason
  FROM __CATALOG__.__SCHEMA__.payments_enriched_silver
  WHERE fraud_score > COALESCE(get_high_risk_transactions.threshold, 0.7)
    AND event_date >= CURRENT_DATE - 1
  ORDER BY fraud_score DESC
  LIMIT 50;

CREATE OR REPLACE FUNCTION __CATALOG__.__SCHEMA__.get_risk_distribution()
RETURNS TABLE(
  risk_tier STRING,
  transaction_count BIGINT,
  approval_rate DOUBLE,
  avg_fraud_score DOUBLE,
  total_value DOUBLE
)
LANGUAGE SQL
COMMENT 'Get risk score distribution across tiers.'
RETURN
  SELECT
    risk_tier,
    COUNT(*) AS transaction_count,
    ROUND(AVG(CASE WHEN is_approved THEN 1.0 ELSE 0.0 END) * 100, 2) AS approval_rate,
    ROUND(AVG(fraud_score), 3) AS avg_fraud_score,
    ROUND(SUM(amount), 2) AS total_value
  FROM __CATALOG__.__SCHEMA__.payments_enriched_silver
  WHERE event_date >= CURRENT_DATE - 7
  GROUP BY risk_tier
  ORDER BY avg_fraud_score DESC;

-- -----------------------------------------------------------------------------
-- Performance Recommender tools
-- -----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION __CATALOG__.__SCHEMA__.get_kpi_summary()
RETURNS TABLE(
  total_transactions BIGINT,
  approval_rate_pct DOUBLE,
  total_transaction_value DOUBLE,
  avg_fraud_score DOUBLE
)
LANGUAGE SQL
COMMENT 'Get current executive KPI summary.'
RETURN
  SELECT
    total_transactions,
    approval_rate_pct,
    total_transaction_value,
    avg_fraud_score
  FROM __CATALOG__.__SCHEMA__.v_executive_kpis;

CREATE OR REPLACE FUNCTION __CATALOG__.__SCHEMA__.get_optimization_opportunities()
RETURNS TABLE(
  optimization_area STRING,
  payment_solution STRING,
  approval_rate_pct DOUBLE,
  transaction_count BIGINT,
  priority STRING
)
LANGUAGE SQL
COMMENT 'Identify optimization opportunities by routing and geography.'
RETURN
  SELECT
    'Routing' AS optimization_area,
    payment_solution,
    approval_rate_pct,
    transaction_count,
    CASE
      WHEN approval_rate_pct < 80 THEN 'HIGH'
      WHEN approval_rate_pct < 85 THEN 'MEDIUM'
      ELSE 'LOW'
    END AS priority
  FROM __CATALOG__.__SCHEMA__.v_solution_performance
  WHERE approval_rate_pct < 90
  UNION ALL
  SELECT
    'Geography' AS optimization_area,
    country AS payment_solution,
    approval_rate_pct,
    transaction_count,
    CASE
      WHEN approval_rate_pct < 80 THEN 'HIGH'
      WHEN approval_rate_pct < 85 THEN 'MEDIUM'
      ELSE 'LOW'
    END AS priority
  FROM __CATALOG__.__SCHEMA__.v_performance_by_geography
  WHERE approval_rate_pct < 85 AND transaction_count > 100
  ORDER BY CASE priority WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END, approval_rate_pct;

CREATE OR REPLACE FUNCTION __CATALOG__.__SCHEMA__.get_trend_analysis()
RETURNS TABLE(
  event_date DATE,
  transaction_count BIGINT,
  approval_rate_pct DOUBLE,
  total_value DOUBLE
)
LANGUAGE SQL
COMMENT 'Get performance trends over time.'
RETURN
  SELECT
    event_date,
    transactions AS transaction_count,
    approval_rate AS approval_rate_pct,
    total_value
  FROM __CATALOG__.__SCHEMA__.v_daily_trends
  ORDER BY event_date DESC
  LIMIT 30;
