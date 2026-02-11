import { Suspense } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useGetDataQualitySummary } from "@/lib/api";
import { getDashboardUrl, openInDatabricks } from "@/config/workspace";
import { AlertTriangle, CheckCircle2, ExternalLink, Gauge } from "lucide-react";

export const Route = createFileRoute("/_sidebar/alerts-data-quality")({
  component: () => (
    <Suspense fallback={<AlertsDataQualitySkeleton />}>
      <AlertsDataQuality />
    </Suspense>
  ),
});

function AlertsDataQualitySkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-64" />
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton className="h-48" />
        <Skeleton className="h-48" />
      </div>
    </div>
  );
}

function AlertsDataQuality() {
  const dataQualityQ = useGetDataQualitySummary();
  const dataQuality = dataQualityQ.data?.data;
  const retentionPct = dataQuality?.retention_pct_24h;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Alerts & Data Quality</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Monitor alerts and data quality checks for payment pipelines
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Alerts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              View and manage real-time alerts and critical incidents in the monitoring dashboard.
            </p>
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => openInDatabricks(getDashboardUrl("/sql/dashboards/realtime_monitoring"))}
              >
                Real-Time Monitoring
                <ExternalLink className="h-3 w-3 ml-2" />
              </Button>
              <Button variant="outline" size="sm" asChild>
                <Link to="/incidents">Incidents</Link>
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Gauge className="h-4 w-4" />
              Data Quality
            </CardTitle>
          </CardHeader>
          <CardContent>
            {dataQualityQ.isLoading ? (
              <Skeleton className="h-32" />
            ) : (
              <ul className="space-y-3 text-sm">
                <li className="flex items-center justify-between gap-2">
                  <span className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                    Data Freshness
                  </span>
                  <span className="tabular-nums font-medium">
                    {retentionPct != null ? `${Math.min(100, retentionPct).toFixed(1)}%` : "—"}
                  </span>
                </li>
                <li className="flex items-center justify-between gap-2">
                  <span className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                    Schema Validation
                  </span>
                  <span className="tabular-nums font-medium">
                    {retentionPct != null ? `${retentionPct.toFixed(1)}%` : "—"}
                  </span>
                </li>
                <li className="flex items-center justify-between gap-2">
                  <span className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                    Retention (24h)
                  </span>
                  <span className="tabular-nums font-medium">
                    {retentionPct != null ? `${retentionPct.toFixed(1)}%` : "—"}
                  </span>
                </li>
              </ul>
            )}
            <Button
              variant="outline"
              size="sm"
              className="mt-4"
              onClick={() => openInDatabricks(getDashboardUrl("/sql/dashboards/streaming_data_quality"))}
            >
              Data Quality Dashboard
              <ExternalLink className="h-3 w-3 ml-2" />
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
