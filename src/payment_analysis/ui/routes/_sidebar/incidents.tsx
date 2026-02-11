import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createIncident,
  listIncidents,
  useGetLastHourPerformance,
  useGetStreamingTps,
  type Incident,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Code2, AlertTriangle, Activity } from "lucide-react";
import { getDashboardUrl, openInDatabricks } from "@/config/workspace";

const REFRESH_MS = 5000;

export const Route = createFileRoute("/_sidebar/incidents")({
  component: () => <Incidents />,
});

const openNotebook = async (notebookId: string) => {
  try {
    const response = await fetch(`/api/notebooks/notebooks/${notebookId}/url`);
    const data = await response.json();
    openInDatabricks(data?.url);
  } catch (error) {
    console.error("Failed to open notebook:", error);
  }
};

const openDashboard = () => {
  openInDatabricks(getDashboardUrl("/sql/dashboards/realtime_monitoring"));
};

function Incidents() {
  const qc = useQueryClient();
  const [category, setCategory] = useState("mid_failure");
  const [key, setKey] = useState("MID=demo");

  const q = useQuery({
    queryKey: ["incidents"],
    queryFn: () => listIncidents(),
  });
  const lastHourQ = useGetLastHourPerformance({ query: { refetchInterval: REFRESH_MS } });
  const tpsQ = useGetStreamingTps({ params: { limit_seconds: 120 }, query: { refetchInterval: REFRESH_MS } });

  const create = useMutation({
    mutationFn: () => createIncident({ category, key, severity: "medium", details: {} }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["incidents"] }),
  });

  const items = q.data?.data ?? [];
  const lastHour = lastHourQ.data?.data;
  const eventsPerSec = lastHour?.transactions_last_hour != null ? Math.round(lastHour.transactions_last_hour / 3600) : null;
  const tpsPoints = tpsQ.data?.data ?? [];
  const latestTps = tpsPoints.length > 0 ? tpsPoints[tpsPoints.length - 1]?.records_per_second : null;

  return (
    <div className="space-y-6">
      <div>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-2xl font-semibold tracking-tight">Real-Time Monitor</h1>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={openDashboard}>
              <AlertTriangle className="w-4 h-4 mr-2" />
              Monitoring Dashboard
              <ExternalLink className="w-3 h-3 ml-2" />
            </Button>
            <Button variant="outline" size="sm" onClick={() => openNotebook("realtime_pipeline")}>
              <Code2 className="w-4 h-4 mr-2" />
              Alert Pipeline
              <ExternalLink className="w-3 h-3 ml-2" />
            </Button>
          </div>
        </div>
        <p className="text-sm text-muted-foreground mt-2">
          Live view: Simulate Transaction Events → Payment Analysis ETL &amp; Payment Real-Time Stream. Refresh every 5s.
        </p>
      </div>

      {/* Real-time stats strip */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card className="border border-[var(--neon-cyan)]/20 bg-[var(--neon-cyan)]/5">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Activity className="h-4 w-4 text-[var(--neon-cyan)]" />
              TPS (live)
            </div>
            <p className="mt-1 text-2xl font-bold tabular-nums text-[var(--neon-cyan)]">
              {tpsQ.isLoading ? "—" : (latestTps ?? eventsPerSec ?? "—")}
            </p>
            <p className="text-xs text-muted-foreground">transactions/sec</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-muted-foreground">Last hour volume</div>
            <p className="mt-1 text-2xl font-bold tabular-nums">
              {lastHourQ.isLoading ? "—" : (lastHour?.transactions_last_hour?.toLocaleString() ?? "—")}
            </p>
            <p className="text-xs text-muted-foreground">approval {lastHour?.approval_rate_pct != null ? `${lastHour.approval_rate_pct.toFixed(1)}%` : "—"}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-muted-foreground">Incidents</div>
            <p className="mt-1 text-2xl font-bold tabular-nums">{items.length}</p>
            <p className="text-xs text-muted-foreground">open + resolved</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Create incident</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 md:grid-cols-3">
          <Input value={category} onChange={(e) => setCategory(e.target.value)} />
          <Input value={key} onChange={(e) => setKey(e.target.value)} />
          <Button onClick={() => create.mutate()} disabled={create.isPending}>
            Create
          </Button>
        </CardContent>
      </Card>

      <div className="space-y-3">
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">No incidents yet.</p>
        ) : (
          items.map((inc) => <IncidentRow key={inc.id} inc={inc} />)
        )}
      </div>
    </div>
  );
}

const MONITORING_DASHBOARD_PATH = "/sql/dashboards/realtime_monitoring";

function IncidentRow({ inc }: { inc: Incident }) {
  const openInWorkspace = () => {
    const url = getDashboardUrl(MONITORING_DASHBOARD_PATH);
    openInDatabricks(url);
  };
  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={openInWorkspace}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && openInWorkspace()}
    >
      <CardHeader className="py-4">
        <CardTitle className="flex items-center justify-between gap-2">
          <div className="min-w-0">
            <div className="truncate">
              {inc.category} — {inc.key}
            </div>
            <div className="text-xs text-muted-foreground font-mono truncate">
              {inc.id}
            </div>
          </div>
          <div className="flex gap-2 items-center">
            <Badge variant="secondary">{inc.severity}</Badge>
            <Badge variant={inc.status === "open" ? "default" : "secondary"}>
              {inc.status}
            </Badge>
            <ExternalLink className="h-4 w-4 text-muted-foreground shrink-0" aria-hidden />
          </div>
        </CardTitle>
        <p className="text-xs text-muted-foreground mt-1">Click to open Real-Time Monitoring in Databricks</p>
      </CardHeader>
    </Card>
  );
}

