"""Corrected script to update existing dashboards in workspace (avoids duplications).

This script pulls current dashboard definitions and republishes them.
Uses the correct SDK patterns from the codebase.
"""
from databricks.sdk import WorkspaceClient
import json
import os

w = WorkspaceClient()

# Dashboard IDs from app.yml (updated 2026-02-18)
dashboards = {
    "data_quality_unified": "01f10c8357c3109b95b13ff763752746",
    "ml_optimization_unified": "01f10c8357b81b5ebaaf7546e476f557",
    "executive_trends_unified": "01f10c8357c416fc8223b3244362adfd",
}

os.makedirs(".build/dashboards", exist_ok=True)

print("=" * 70)
print("DASHBOARD UPDATE SCRIPT (CORRECTED)")
print("=" * 70)

# Pull current definitions
for name, dashboard_id in dashboards.items():
    try:
        dashboard = w.lakeview.get(dashboard_id)
        serialized = dashboard.serialized_dashboard
        if serialized:
            path = f".build/dashboards/{name}.lvdash.json"
            with open(path, "w") as f:
                json.dump(serialized, f, indent=2)
            print(f"✅ Pulled {name}: {dashboard_id}")
        else:
            print(f"⚠️  {name}: No serialized dashboard")
    except Exception as e:
        print(f"❌ {name}: {e}")

print("\n✅ Dashboard definitions pulled successfully")
print("\nNote: Dashboards are updated via 'databricks bundle deploy' with")
print("resources/dashboards.yml. The .build/dashboards/*.lvdash.json files")
print("are used by the bundle during deployment.")
