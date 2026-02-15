import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  createExperiment,
  listExperimentsKey,
  useListExperiments,
  useGetExperimentResults,
  startExperiment,
  stopExperiment,
  type Experiment,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { ExternalLink, Code2, FlaskConical, TrendingUp, TrendingDown, BarChart3, CheckCircle2 } from "lucide-react";
import { getMLflowUrl, openInDatabricks } from "@/config/workspace";
import { openNotebookInDatabricks } from "@/lib/notebooks";

function ExperimentsErrorFallback({ error, resetErrorBoundary }: { error: unknown; resetErrorBoundary: () => void }) {
  return (
    <div className="p-6">
      <Card className="glass-card border border-border/80 border-l-4 border-l-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Something went wrong</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-sm text-muted-foreground">{error instanceof Error ? error.message : String(error)}</p>
          <Button variant="outline" size="sm" onClick={resetErrorBoundary}>Try again</Button>
        </CardContent>
      </Card>
    </div>
  );
}

export const Route = createFileRoute("/_sidebar/experiments")({
  component: () => (
    <ErrorBoundary FallbackComponent={ExperimentsErrorFallback}>
      <Experiments />
    </ErrorBoundary>
  ),
});

function Experiments() {
  const qc = useQueryClient();
  const [name, setName] = useState("Routing bandit v0");

  const q = useListExperiments({ query: { refetchInterval: 30_000 } });

  const create = useMutation({
    mutationFn: () => createExperiment({ name }),
    onSuccess: () => qc.invalidateQueries({ queryKey: listExperimentsKey() }),
  });
  const start = useMutation({
    mutationFn: (experiment_id: string) => startExperiment({ experiment_id }),
    onSuccess: () => qc.invalidateQueries({ queryKey: listExperimentsKey() }),
  });
  const stop = useMutation({
    mutationFn: (experiment_id: string) => stopExperiment({ experiment_id }),
    onSuccess: () => qc.invalidateQueries({ queryKey: listExperimentsKey() }),
  });

  const items = q.data?.data ?? [];

  return (
    <div className="space-y-6">
      {/* Header with Links */}
      <div>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Experiments</h1>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => openNotebookInDatabricks("train_models")}
            >
              <FlaskConical className="w-4 h-4 mr-2" />
              ML Training
              <ExternalLink className="w-3 h-3 ml-2" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => openNotebookInDatabricks("agent_framework")}
            >
              <Code2 className="w-4 h-4 mr-2" />
              Agent Tests
              <ExternalLink className="w-3 h-3 ml-2" />
            </Button>
          </div>
        </div>
        <p className="text-sm text-muted-foreground mt-2">
          A/B testing and routing experiments with MLflow tracking
        </p>
      </div>

      <Card className="glass-card border border-border/80">
        <CardHeader>
          <CardTitle>Create experiment</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2">
          <Input value={name} onChange={(e) => setName(e.target.value)} />
          <Button onClick={() => create.mutate()} disabled={create.isPending}>
            Create
          </Button>
        </CardContent>
      </Card>

      <div className="space-y-3">
        {q.isLoading ? (
          <>
            {[1, 2, 3].map((i) => (
              <Card key={i} className="glass-card border border-border/80">
                <CardHeader className="py-4 space-y-2">
                  <Skeleton className="h-5 w-48" />
                  <Skeleton className="h-3 w-32" />
                </CardHeader>
                <CardContent className="flex gap-2">
                  <Skeleton className="h-9 w-16" />
                  <Skeleton className="h-9 w-16" />
                </CardContent>
              </Card>
            ))}
          </>
        ) : items.length === 0 ? (
          <Card className="glass-card border border-border/80">
            <CardContent className="py-8 text-center">
              <FlaskConical className="w-10 h-10 mx-auto text-muted-foreground mb-3" />
              <p className="text-sm text-muted-foreground">No experiments yet. Create one above.</p>
            </CardContent>
          </Card>
        ) : (
          items.map((exp) => (
            <ExperimentRow
              key={exp.id ?? exp.name}
              exp={exp}
              onStart={() => exp.id && start.mutate(exp.id)}
              onStop={() => exp.id && stop.mutate(exp.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}

function ExperimentRow({
  exp,
  onStart,
  onStop,
}: {
  exp: Experiment;
  onStart: () => void;
  onStop: () => void;
}) {
  const id = exp.id ?? "";
  const [showResults, setShowResults] = useState(false);
  const openInWorkspace = () => openInDatabricks(getMLflowUrl());
  return (
    <Card className="glass-card border border-border/80">
      <CardHeader
        className="py-4 cursor-pointer hover:bg-muted/30 transition-colors"
        onClick={openInWorkspace}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && openInWorkspace()}
      >
        <CardTitle className="flex items-center justify-between gap-2">
          <div className="min-w-0">
            <div className="truncate">{exp.name}</div>
            <div className="text-xs text-muted-foreground font-mono truncate">
              {id || "(no id)"}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={exp.status === "running" ? "default" : "secondary"}>
              {exp.status}
            </Badge>
            <ExternalLink className="h-4 w-4 text-muted-foreground shrink-0" aria-hidden />
          </div>
        </CardTitle>
        <p className="text-xs text-muted-foreground mt-1">Click to open MLflow in Databricks</p>
      </CardHeader>
      <CardContent className="space-y-3" onClick={(e) => e.stopPropagation()}>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={onStart}
            disabled={!id || exp.status === "running"}
          >
            Start
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={onStop}
            disabled={!id || exp.status !== "running"}
          >
            Stop
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowResults(!showResults)}
            className="ml-auto"
          >
            <BarChart3 className="w-4 h-4 mr-1" />
            {showResults ? "Hide results" : "View results"}
          </Button>
        </div>
        {showResults && id && <ExperimentResults experimentId={id} />}
      </CardContent>
    </Card>
  );
}


function ExperimentResults({ experimentId }: { experimentId: string }) {
  const { data, isLoading, isError } = useGetExperimentResults({
    params: { experiment_id: experimentId },
  });
  const results = data?.data;

  if (isLoading) return <Skeleton className="h-24 w-full rounded-lg" />;
  if (isError || !results) return <p className="text-xs text-muted-foreground">Could not load results.</p>;

  const hasData = results.control?.outcomes || results.treatment?.outcomes;

  return (
    <div className="space-y-3 pt-2 border-t border-border/50">
      {!hasData ? (
        <p className="text-sm text-muted-foreground">No decision outcomes recorded yet. Run decisions with this experiment active to collect data.</p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3">
            {results.control && (
              <div className="rounded-lg bg-muted/50 p-3 space-y-1">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Control</p>
                <p className="text-lg font-bold tabular-nums">
                  {results.control.approval_rate != null ? `${(results.control.approval_rate * 100).toFixed(1)}%` : "—"}
                </p>
                <p className="text-xs text-muted-foreground">{results.control.outcomes} outcomes · {results.control.subjects} subjects</p>
              </div>
            )}
            {results.treatment && (
              <div className="rounded-lg bg-muted/50 p-3 space-y-1">
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Treatment</p>
                <p className="text-lg font-bold tabular-nums">
                  {results.treatment.approval_rate != null ? `${(results.treatment.approval_rate * 100).toFixed(1)}%` : "—"}
                </p>
                <p className="text-xs text-muted-foreground">{results.treatment.outcomes} outcomes · {results.treatment.subjects} subjects</p>
              </div>
            )}
          </div>

          {results.lift_pct != null && (
            <div className="flex items-center gap-2">
              {results.lift_pct > 0 ? (
                <TrendingUp className="w-4 h-4 text-green-500" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-500" />
              )}
              <span className={`text-sm font-medium ${results.lift_pct > 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}`}>
                {results.lift_pct > 0 ? "+" : ""}{results.lift_pct.toFixed(1)}% lift
              </span>
              {results.p_value != null && (
                <Badge variant={results.is_significant ? "default" : "outline"} className="text-[10px]">
                  p={results.p_value.toFixed(4)}
                </Badge>
              )}
              {results.is_significant && (
                <CheckCircle2 className="w-4 h-4 text-green-500" />
              )}
            </div>
          )}

          <Alert className={results.is_significant ? "border-green-500/50 bg-green-500/5" : ""}>
            <AlertTitle className="text-sm">Recommendation</AlertTitle>
            <AlertDescription className="text-xs">{results.recommendation}</AlertDescription>
          </Alert>
        </>
      )}
    </div>
  );
}

