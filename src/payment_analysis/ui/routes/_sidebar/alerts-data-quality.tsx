import { Suspense } from "react";
import type { CSSProperties } from "react";
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

const REFRESH_MS = 5000;

function AlertsDataQuality() {
  const dataQualityQ = useGetDataQualitySummary({ query: { refetchInterval: REFRESH_MS } });
  const dataQuality = dataQualityQ.data?.data;
  const retentionPct = dataQuality?.retention_pct_24h;
  const dqScore = retentionPct != null ? Math.min(100, Math.round(retentionPct)) : null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Alerts & Data Quality</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Streaming &amp; data quality from Unity Catalog. Refresh every 5s.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="border border-border/80">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-[var(--getnet-red)]" />
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

        <Card className="border-2 border-[var(--neon-cyan)]/30 bg-[var(--neon-cyan)]/5">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Gauge className="h-4 w-4 text-[var(--neon-cyan)]" />
              Data Quality Health
            </CardTitle>
          </CardHeader>
          <CardContent>
            {dataQualityQ.isLoading ? (
              <Skeleton className="h-32 w-full" />
            ) : (
              <>
                <div className="mb-4 flex items-center gap-3">
                  <div
                    className="gauge-conic-cyan h-16 w-16 rounded-full border-2 border-[var(--neon-cyan)]/50 flex items-center justify-center text-xl font-bold tabular-nums text-neon-cyan"
                    style={{ ["--gauge-pct"]: `${dqScore ?? 0}%` } as CSSProperties}
                  >
                    <span className="bg-card rounded-full h-12 w-12 flex items-center justify-center text-sm">
                      {dqScore != null ? `${dqScore}%` : "—"}
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Freshness · Schema · PII masking (Unity Catalog)
                  </div>
                </div>
                <ul className="space-y-3 text-sm">
                  <li className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                      Retention (24h)
                    </span>
                    <span className="tabular-nums font-medium">
                      {retentionPct != null ? `${retentionPct.toFixed(1)}%` : "—"}
                    </span>
                  </li>
                  <li className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                      Bronze (24h)
                    </span>
                    <span className="tabular-nums font-medium">
                      {dataQuality?.bronze_last_24h != null ? dataQuality.bronze_last_24h.toLocaleString() : "—"}
                    </span>
                  </li>
                  <li className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                      Silver (24h)
                    </span>
                    <span className="tabular-nums font-medium">
                      {dataQuality?.silver_last_24h != null ? dataQuality.silver_last_24h.toLocaleString() : "—"}
                    </span>
                  </li>
                </ul>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-4"
                  onClick={() => openInDatabricks(getDashboardUrl("/sql/dashboards/streaming_data_quality"))}
                >
                  Data Quality Dashboard
                  <ExternalLink className="h-3 w-3 ml-2" />
                </Button>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
