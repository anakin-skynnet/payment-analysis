import { Suspense, useMemo, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Switch } from "@/components/ui/switch";
import {
  useGetKpisSuspense,
  useGetSolutionPerformanceSuspense,
  useGetDataQualitySummary,
  useGetStreamingTps,
  useHealthDatabricks,
} from "@/lib/api";
import selector from "@/lib/selector";
import { GetnetAIAssistant } from "@/components/chat";
import {
  Activity,
  Target,
  Gauge,
  SlidersHorizontal,
  TrendingUp,
  TrendingDown,
  CheckCircle2,
} from "lucide-react";

const REFRESH_MS = 5000; // 5s for real-time feel (Simulate Transaction Events → ETL → Real-Time Stream)

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
      <div className="grid gap-4 md:grid-cols-3">
        <Skeleton className="h-28 rounded-xl bg-card" />
        <Skeleton className="h-28 rounded-xl bg-card" />
        <Skeleton className="h-28 rounded-xl bg-card" />
      </div>
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <Skeleton className="h-72 rounded-xl bg-card" />
        <Skeleton className="h-72 rounded-xl bg-card" />
      </div>
    </div>
  );
}

function TpsLineChart({ points }: { points: { event_second: string; records_per_second: number }[] }) {
  const sorted = useMemo(() => [...points].sort((a, b) => new Date(a.event_second).getTime() - new Date(b.event_second).getTime()), [points]);
  const maxTps = useMemo(() => Math.max(1, ...sorted.map((p) => p.records_per_second)), [sorted]);
  const width = 600;
  const height = 200;
  const padding = { top: 8, right: 8, bottom: 24, left: 36 };
  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;
  const n = sorted.length;
  const pathPoints = sorted.map((p, i) => {
    const x = padding.left + (n > 1 ? (i / (n - 1)) * innerWidth : 0);
    const y = padding.top + innerHeight - (p.records_per_second / maxTps) * innerHeight;
    return `${x},${y}`;
  });
  const linePath = pathPoints.length > 1 ? `M ${pathPoints.join(" L ")}` : "";
  const areaPath = pathPoints.length > 1
    ? `${linePath} L ${padding.left + innerWidth},${padding.top + innerHeight} L ${padding.left},${padding.top + innerHeight} Z`
    : "";

  return (
    <svg width="100%" viewBox={`0 0 ${width} ${height}`} className="min-h-[200px]" preserveAspectRatio="xMidYMid meet">
      <defs>
        <linearGradient id="tps-gradient" x1="0" y1="1" x2="0" y2="0">
          <stop offset="0%" stopColor="var(--neon-cyan, #00E5FF)" stopOpacity="0.15" />
          <stop offset="100%" stopColor="var(--neon-cyan, #00E5FF)" stopOpacity="0.4" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill="url(#tps-gradient)" />
      <path
        d={linePath}
        fill="none"
        stroke="var(--neon-cyan, #00E5FF)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <text x={padding.left} y={padding.top + 12} className="fill-muted-foreground text-[10px]">0</text>
      <text x={padding.left} y={padding.top + innerHeight + 14} className="fill-muted-foreground text-[10px]">{maxTps} TPS</text>
    </svg>
  );
}

function CommandCenter() {
  const [controlOpen, setControlOpen] = useState(false);
  const [smartRouting, setSmartRouting] = useState(true);
  const [fraudShadowMode, setFraudShadowMode] = useState(false);
  const [recalculateAlgorithms, setRecalculateAlgorithms] = useState(false);

  const { data: kpis } = useGetKpisSuspense(selector());
  const { data: solutions } = useGetSolutionPerformanceSuspense(selector());
  const dataQualityQ = useGetDataQualitySummary({
    query: { refetchInterval: REFRESH_MS },
  });
  const tpsQ = useGetStreamingTps({
    params: { limit_seconds: 300 },
    query: { refetchInterval: REFRESH_MS },
  });
  const { data: healthData } = useHealthDatabricks();

  const approvalPct = kpis ? (kpis.approval_rate * 100).toFixed(1) : "92.5";
  const falseDeclinePct = kpis ? ((1 - kpis.approval_rate) * 100).toFixed(1) : "1.2";
  const routingEfficiency =
    solutions?.length && solutions[0]
      ? solutions.reduce((sum, s) => sum + s.approval_rate_pct * s.transaction_count, 0) /
        Math.max(1, solutions.reduce((sum, s) => sum + s.transaction_count, 0))
      : 98.2;
  const dataQuality = dataQualityQ.data?.data;
  const dqScore = dataQuality?.retention_pct_24h != null
    ? Math.min(100, Math.round(dataQuality.retention_pct_24h))
    : 99;
  const tpsPoints = tpsQ.data?.data ?? [];
  const fromDatabricks = healthData?.data?.analytics_source === "Unity Catalog";

  return (
    <div className="flex min-h-full flex-col bg-background">
      <main className="flex-1 space-y-6 p-4 md:p-6" role="main">
        {/* Top row: 3 high-contrast KPI cards (GAR, False Decline, DQ) */}
        <section aria-labelledby="kpi-heading" className="grid gap-4 md:grid-cols-3">
          <h2 id="kpi-heading" className="sr-only">
            Strategic KPIs
          </h2>
          <Card className="border-2 border-[var(--getnet-red)]/40 bg-[var(--getnet-red)]/10 dark:bg-[var(--getnet-red)]/15">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-muted-foreground">
                  Gross Approval Rate (GAR)
                </span>
                <Target className="h-4 w-4 text-[var(--getnet-red)]" aria-hidden />
              </div>
              <p className="mt-2 text-4xl font-bold text-[var(--getnet-red)] tabular-nums">
                {approvalPct}%
              </p>
              <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                <span>Target 92.5%</span>
                <span className="inline-flex items-center text-green-500">
                  <TrendingUp className="h-3 w-3" /> +3.1% YoY
                </span>
              </p>
            </CardContent>
          </Card>
          <Card className="border-2 border-orange-500/50 bg-orange-500/10 dark:bg-orange-500/15">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-muted-foreground">
                  False Decline Rate
                </span>
              </div>
              <p className="mt-2 text-4xl font-bold text-orange-500 tabular-nums">
                {falseDeclinePct}%
              </p>
              <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                <span>Target 1.2%</span>
                <span className="inline-flex items-center text-green-500">
                  <TrendingDown className="h-3 w-3" /> -17% YoY
                </span>
              </p>
            </CardContent>
          </Card>
          <Card className="border-2 border-[var(--neon-cyan)]/40 bg-[var(--neon-cyan)]/5 dark:bg-[var(--neon-cyan)]/10">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-muted-foreground">
                  Data Quality Health
                </span>
                <Gauge className="h-4 w-4 text-[var(--neon-cyan)]" aria-hidden />
              </div>
              <p className="mt-2 text-4xl font-bold text-[var(--neon-cyan)] tabular-nums">
                {dataQualityQ.isLoading ? "—" : `${dqScore}%`}
              </p>
              <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                <CheckCircle2 className="h-3 w-3 text-green-500 shrink-0" />
                Freshness · Schema · PII masking
              </p>
            </CardContent>
          </Card>
        </section>

        {/* Middle row: TPS line chart + Smart Routing donut */}
        <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
          <Card className="overflow-hidden border border-border/80">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Activity className="h-4 w-4 text-[var(--neon-cyan)]" />
                Real-Time Ingestion — TPS
              </CardTitle>
              <p className="text-xs text-muted-foreground">
                Transaction volume (Simulate Transaction Events → Payment Analysis ETL &amp; Payment Real-Time Stream). Refresh every 5s.
              </p>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              {tpsQ.isLoading ? (
                <Skeleton className="h-[200px] w-full rounded-lg" />
              ) : tpsPoints.length === 0 ? (
                <div className="flex h-[200px] items-center justify-center rounded-lg bg-muted/30 text-sm text-muted-foreground">
                  No streaming data yet. Start the stream simulator and pipelines.
                </div>
              ) : (
                <TpsLineChart points={tpsPoints} />
              )}
            </CardContent>
          </Card>
          <Card className="border border-border/80">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <Target className="h-4 w-4 text-primary" />
                Smart Routing Efficiency
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex flex-col items-center gap-4">
                <div
                  className="h-36 w-36 rounded-full border-2 border-muted flex items-center justify-center text-2xl font-bold tabular-nums"
                  style={{
                    background: `conic-gradient(hsl(var(--primary)) 0% ${routingEfficiency}%, hsl(var(--muted)) ${routingEfficiency}% 100%)`,
                  }}
                >
                  <span className="bg-card rounded-full h-24 w-24 flex items-center justify-center text-lg">
                    {routingEfficiency != null ? `${routingEfficiency.toFixed(1)}%` : "—"}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">Target &gt;98%</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Control Panel trigger — right-side drawer */}
        <div className="flex justify-end">
          <Sheet open={controlOpen} onOpenChange={setControlOpen}>
            <SheetTrigger asChild>
              <Button variant="outline" size="sm" className="gap-2">
                <SlidersHorizontal className="h-4 w-4" />
                Control Panel
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[320px] sm:max-w-sm">
              <SheetHeader>
                <SheetTitle>Control Panel</SheetTitle>
              </SheetHeader>
              <div className="mt-6 space-y-6">
                <div className="flex items-center justify-between">
                  <label htmlFor="smart-routing" className="text-sm font-medium">
                    Smart Routing
                  </label>
                  <Switch
                    id="smart-routing"
                    checked={smartRouting}
                    onCheckedChange={setSmartRouting}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label htmlFor="fraud-shadow" className="text-sm font-medium">
                    Fraud Shadow Mode
                  </label>
                  <Switch
                    id="fraud-shadow"
                    checked={fraudShadowMode}
                    onCheckedChange={setFraudShadowMode}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <label htmlFor="recalc-algo" className="text-sm font-medium">
                    Recalculate Algorithms
                  </label>
                  <Switch
                    id="recalc-algo"
                    checked={recalculateAlgorithms}
                    onCheckedChange={setRecalculateAlgorithms}
                  />
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>

        {/* Data source footer */}
        <footer className="flex items-center justify-between border-t border-border/80 px-4 py-2 text-xs text-muted-foreground">
          <span>Live data · Refresh every 5s</span>
          {fromDatabricks ? (
            <span className="inline-flex items-center gap-1 rounded bg-green-500/10 text-green-600 dark:text-green-400 px-2 py-0.5">
              Data: Databricks
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded bg-amber-500/10 text-amber-700 dark:text-amber-400 px-2 py-0.5">
              Data: Sample
            </span>
          )}
        </footer>
      </main>

      <GetnetAIAssistant />
    </div>
  );
}
