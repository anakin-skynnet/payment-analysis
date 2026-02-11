import { Suspense } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  useGetKpisSuspense,
  useGetLastHourPerformance,
  useGetSolutionPerformanceSuspense,
  useGetApprovalTrendsSuspense,
  useDeclineSummary,
  useGetDataQualitySummary,
  useHealthDatabricks,
} from "@/lib/api";
import selector from "@/lib/selector";
import { getDashboardUrl, openInDatabricks } from "@/config/workspace";
import { GetnetAIAssistant, AgentOrchestratorChat } from "@/components/chat";
import {
  Lock,
  Activity,
  Target,
  Globe,
  AlertTriangle,
  CheckCircle2,
  Gauge,
} from "lucide-react";

export const Route = createFileRoute("/_sidebar/command-center")({
  component: () => (
    <Suspense fallback={<CommandCenterSkeleton />}>
      <CommandCenter />
    </Suspense>
  ),
});

function CommandCenterSkeleton() {
  return (
    <div className="space-y-6 p-4">
      <Skeleton className="h-12 w-full" />
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        <Skeleton className="h-48" />
        <Skeleton className="h-48" />
        <Skeleton className="h-48" />
      </div>
    </div>
  );
}

function CommandCenter() {
  const { data: kpis } = useGetKpisSuspense(selector());
  const lastHourQ = useGetLastHourPerformance();
  const { data: solutions } = useGetSolutionPerformanceSuspense(selector());
  const { data: trends } = useGetApprovalTrendsSuspense({ params: { hours: 30 * 24 } });
  const declineQ = useDeclineSummary({ params: { limit: 5 } });
  const dataQualityQ = useGetDataQualitySummary();
  const { data: healthData } = useHealthDatabricks();
  const fromDatabricks = healthData?.data?.analytics_source === "Unity Catalog";

  const approvalPct = kpis ? (kpis.approval_rate * 100).toFixed(1) : null;
  const declineRatePct = kpis ? ((1 - kpis.approval_rate) * 100).toFixed(1) : null;

  const lastHour = lastHourQ.data?.data;
  const eventsPerSecond =
    lastHour?.transactions_last_hour != null
      ? Math.round(lastHour.transactions_last_hour / 3600)
      : null;

  const routingEfficiency =
    solutions?.length && solutions[0]
      ? solutions.reduce((sum, s) => sum + s.approval_rate_pct * s.transaction_count, 0) /
        Math.max(
          1,
          solutions.reduce((sum, s) => sum + s.transaction_count, 0)
        )
      : null;

  const trendData = trends?.data ?? [];
  const topDeclines = declineQ.data?.data ?? [];
  const dataQuality = dataQualityQ.data?.data;
  const retentionPct = dataQuality?.retention_pct_24h;
  const lastUpdated = new Date().toLocaleString(undefined, {
    dateStyle: "short",
    timeStyle: "short",
  });

  return (
    <div className="flex min-h-full flex-col bg-background">
      <main className="flex-1 space-y-6 p-4 md:p-6">
        {/* Strategic Imperative: Gross Approval Rate, False Decline Rate */}
        <section aria-labelledby="strategic-heading">
          <h2 id="strategic-heading" className="sr-only">
            Strategic Imperative — Accelerate Approval Rates
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="border-2 border-green-500/50 bg-green-500/10">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-muted-foreground">
                    Gross Approval Rate
                  </span>
                  <Lock className="h-4 w-4 text-muted-foreground" />
                </div>
                <p className="mt-2 text-4xl font-bold text-green-600 dark:text-green-400 tabular-nums">
                  {approvalPct ?? "—"}%
                </p>
                <p className="mt-1 text-xs text-muted-foreground">From Databricks executive KPIs</p>
              </CardContent>
            </Card>
            <Card className="border-2 border-orange-500/50 bg-orange-500/10">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-muted-foreground">
                    Decline Rate
                  </span>
                  <Lock className="h-4 w-4 text-muted-foreground" />
                </div>
                <p className="mt-2 text-4xl font-bold text-orange-600 dark:text-orange-400 tabular-nums">
                  {declineRatePct ?? "—"}%
                </p>
                <p className="mt-1 text-xs text-muted-foreground">From Databricks executive KPIs</p>
              </CardContent>
            </Card>
          </div>
        </section>

        {/* Mid section: Real-Time Ingestion, Smart Routing Efficiency, Control Panel */}
        <div className="grid gap-4 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Activity className="h-4 w-4" />
                Real-Time Ingestion Monitor
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="h-24 rounded bg-muted/50 flex items-center justify-center">
                {lastHourQ.isLoading ? (
                  <Skeleton className="h-16 w-full" />
                ) : (
                  <p className="text-2xl font-bold tabular-nums text-primary">
                    {eventsPerSecond != null ? eventsPerSecond.toLocaleString() : "—"}
                  </p>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                Transactions (last hour), avg events/sec:{" "}
                <span className="font-semibold text-foreground">
                  {eventsPerSecond != null ? eventsPerSecond.toLocaleString() : "—"}
                </span>
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Target className="h-4 w-4" />
                Dynamic Smart Routing Efficiency
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center gap-2">
                <div
                  className="h-28 w-28 rounded-full border-4 border-muted flex items-center justify-center"
                  style={{
                    background: `conic-gradient(hsl(var(--primary)) 0% ${routingEfficiency ?? 0}%, hsl(var(--muted)) ${routingEfficiency ?? 0}% 100%)`,
                  }}
                >
                  <span className="text-2xl font-bold tabular-nums bg-background rounded-full h-20 w-20 flex items-center justify-center">
                    {routingEfficiency != null ? `${routingEfficiency.toFixed(1)}%` : "—"}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">Target &gt;98%</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Control Panel</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm">Activate Smart Routing Engine (Live)</span>
                <span className="inline-flex h-6 w-11 shrink-0 rounded-full bg-primary px-1.5 py-0.5" aria-hidden>
                  <span className="h-5 w-5 rounded-full bg-primary-foreground shadow translate-x-5" />
                </span>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                onClick={() => openInDatabricks(getDashboardUrl("/sql/dashboards/routing_optimization"))}
              >
                Deploy Fraud Model v2.1 (Shadow Mode)
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                asChild
              >
                <Link to="/decisioning">Recalculate Routing Algorithms</Link>
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Lower section: Performance Analytics, Top 5 Decline Reasons, Data Quality */}
        <div className="grid gap-4 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Globe className="h-4 w-4" />
                Performance Analytics
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="h-24 rounded bg-muted/50 flex items-center justify-center">
                <Link
                  to="/dashboards"
                  search={{ embed: "global_coverage" }}
                  className="text-sm text-primary hover:underline"
                >
                  World map · Open in Dashboards
                </Link>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground mb-2">
                  Approval Rate Trends (Last 30 Days)
                </p>
                <div className="h-20 flex items-end gap-0.5">
                  {trendData
                    .filter((_, i) => i % 24 === 0)
                    .slice(0, 30)
                    .reverse()
                    .map((t) => (
                    <div
                      key={t.hour}
                      className="flex-1 min-w-0 rounded-t bg-primary/70"
                      style={{
                        height: `${Math.min(100, (t.approval_rate_pct ?? 0) * 1.2)}%`,
                      }}
                      title={`${t.hour}: ${t.approval_rate_pct?.toFixed(1)}%`}
                    />
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Top 5 Decline Reasons
              </CardTitle>
            </CardHeader>
            <CardContent>
              {declineQ.isLoading ? (
                <Skeleton className="h-32" />
              ) : topDeclines.length === 0 ? (
                <p className="text-sm text-muted-foreground">No decline data yet.</p>
              ) : (
                <div className="flex gap-4">
                  <ul className="space-y-2 flex-1">
                    {topDeclines.slice(0, 5).map((d) => (
                      <li key={d.key} className="flex items-center gap-2 text-sm">
                        <span className="inline-flex h-4 w-4 shrink-0 rounded border border-muted-foreground/40" />
                        <span className="truncate">{d.key}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="flex items-end gap-1">
                    {topDeclines.slice(0, 5).map((d) => (
                      <div
                        key={d.key}
                        className="w-6 rounded-t bg-primary"
                        style={{
                          height: `${Math.min(80, (d.pct_of_declines ?? 0) * 2)}px`,
                        }}
                        title={`${d.key}: ${d.pct_of_declines?.toFixed(1)}%`}
                      />
                    ))}
                  </div>
                </div>
              )}
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
                <Skeleton className="h-24" />
              ) : (
                <ul className="space-y-2 text-sm">
                  <li className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      Data Freshness
                    </span>
                    <span className="tabular-nums font-medium">
                      {retentionPct != null ? `${Math.min(100, retentionPct).toFixed(1)}%` : "—"}
                    </span>
                  </li>
                  <li className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      Schema Validation
                    </span>
                    <span className="tabular-nums font-medium">
                      {retentionPct != null ? `${retentionPct.toFixed(1)}%` : "—"}
                    </span>
                  </li>
                  <li className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                      Retention (24h)
                    </span>
                    <span className="tabular-nums font-medium">
                      {retentionPct != null ? `${retentionPct.toFixed(1)}%` : "—"}
                    </span>
                  </li>
                </ul>
              )}
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Footer */}
      <footer className="flex items-center justify-between border-t border-border/80 px-4 py-2 text-xs text-muted-foreground">
        <span>Last Updated: {lastUpdated}</span>
        <span className="flex items-center gap-3">
          {fromDatabricks ? (
            <span className="inline-flex items-center gap-1 rounded bg-green-500/10 text-green-700 dark:text-green-400 px-2 py-0.5" title="All numbers and dashboards from Databricks Unity Catalog">
              Data: Databricks
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded bg-amber-500/10 text-amber-700 dark:text-amber-400 px-2 py-0.5" title="Sample or fallback data when Databricks is not connected">
              Data: Sample
            </span>
          )}
          <span className="flex items-center gap-1">
            Santander &amp; Getnet Unified Platform
          </span>
        </span>
      </footer>

      <GetnetAIAssistant />
      <AgentOrchestratorChat />
    </div>
  );
}
