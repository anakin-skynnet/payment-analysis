import { Database } from "lucide-react";
import { cn } from "@/lib/utils";

interface DataSourceBadgeProps {
  className?: string;
  /** Short label, e.g. "From Databricks" or "Live from workspace" */
  label?: string;
}

/**
 * Small badge indicating that the data on the page is fetched from the user's Databricks workspace.
 * Use on pages that display API-backed data (KPIs, models, dashboards, etc.).
 */
export function DataSourceBadge({ className, label = "From Databricks" }: DataSourceBadgeProps) {
  return (
    <span
      className={cn("data-source-badge", className)}
      title="Data and results are loaded from your Databricks workspace (Unity Catalog, Lakehouse, MLflow)"
    >
      <Database className="h-3 w-3 shrink-0" aria-hidden />
      <span>{label}</span>
    </span>
  );
}
