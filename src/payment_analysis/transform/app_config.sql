-- ============================================================================
-- App config table (Lakehouse) – catalog and schema used by the app
-- ============================================================================
-- Run in the same catalog/schema as other Lakehouse tables (bootstrap from env:
-- DATABRICKS_CATALOG / DATABRICKS_SCHEMA). The app reads this table to get
-- the effective catalog and schema for all operations (analytics, rules, ML).
-- UI can update catalog/schema; values are persisted here and used app-wide.
-- ============================================================================

CREATE TABLE IF NOT EXISTS app_config (
    id INT NOT NULL DEFAULT 1,
    catalog STRING NOT NULL COMMENT 'Unity Catalog name used by the app',
    schema STRING NOT NULL COMMENT 'Schema name used by the app',
    updated_at TIMESTAMP NOT NULL DEFAULT current_timestamp()
)
USING DELTA
TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
COMMENT 'Single-row config: catalog and schema for the Payment Approval app. Updated via UI or API.';

-- Seed default row only when table is empty (bootstrap catalog/schema)
INSERT INTO app_config (id, catalog, schema)
SELECT 1, 'ahs_demos_catalog', 'ahs_demo_payment_analysis_dev'
WHERE (SELECT COUNT(*) FROM app_config) = 0;
