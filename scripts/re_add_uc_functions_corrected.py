"""Corrected script to re-add UC function resources after bundle deploy.

NOTE: UC Functions cannot be added via the Apps SDK directly.
They must be added manually via:
1. Databricks Apps UI: Compute → Apps → payment-analysis → Configure → App resources
2. Or use the Databricks CLI/API directly with proper resource structure

This script verifies current state and provides instructions.
"""
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

print("=" * 70)
print("UC FUNCTION RESOURCES VERIFICATION")
print("=" * 70)

app = w.apps.get("payment-analysis")
current_resources = list(app.resources) if app.resources else []

print(f"\nApp: {app.name}")
print(f"Total resources: {len(current_resources)}")

# UC Functions that should be present
uc_functions = [
    "ahs_demos_catalog.payment_analysis.get_cascade_recommendations",
    "ahs_demos_catalog.payment_analysis.get_decline_by_segment",
    "ahs_demos_catalog.payment_analysis.get_decline_trends",
    "ahs_demos_catalog.payment_analysis.get_high_risk_transactions",
    "ahs_demos_catalog.payment_analysis.get_kpi_summary",
    "ahs_demos_catalog.payment_analysis.get_optimization_opportunities",
    "ahs_demos_catalog.payment_analysis.get_recovery_opportunities",
    "ahs_demos_catalog.payment_analysis.get_retry_success_rates",
    "ahs_demos_catalog.payment_analysis.get_risk_distribution",
    "ahs_demos_catalog.payment_analysis.get_route_performance",
    "ahs_demos_catalog.payment_analysis.get_trend_analysis",
]

# Check existing functions
existing_funcs = set()
for res in current_resources:
    uc = getattr(res, 'uc_securable', None)
    if uc:
        sec_type = getattr(uc, 'securable_type', None)
        if sec_type == "FUNCTION":
            full_name = getattr(uc, 'securable_full_name', None)
            if full_name:
                existing_funcs.add(full_name)

print(f"\nExisting UC Functions: {len(existing_funcs)}")
for func in sorted(existing_funcs):
    print(f"  ✅ {func}")

missing = [f for f in uc_functions if f not in existing_funcs]
if missing:
    print(f"\n⚠️  Missing UC Functions ({len(missing)}):")
    for func in missing:
        print(f"  ❌ {func}")
    
    print("\n" + "=" * 70)
    print("TO ADD MISSING FUNCTIONS:")
    print("=" * 70)
    print("\nOption 1: Via Databricks Apps UI")
    print("  1. Go to: Compute → Apps → payment-analysis")
    print("  2. Click 'Configure' → 'App resources'")
    print("  3. Click 'Add resource' → 'Unity Catalog function'")
    print("  4. For each missing function:")
    print("     - Securable type: FUNCTION")
    print("     - Securable full name: <function_name>")
    print("     - Permission: EXECUTE")
    print("\nOption 2: Via Databricks CLI (if supported)")
    print("  Use: databricks apps update --resources <json_file>")
    print("\nNote: The Databricks SDK doesn't support updating app resources")
    print("directly. Use the UI or CLI instead.")
else:
    print("\n✅ All UC functions are present!")

print("\n" + "=" * 70)
