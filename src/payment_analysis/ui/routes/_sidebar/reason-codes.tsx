import { createFileRoute } from "@tanstack/react-router";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  useGetReasonCodeInsightsBr,
  useGetEntrySystemDistributionBr,
} from "@/lib/api";

export const Route = createFileRoute("/_sidebar/reason-codes")({
  component: () => <ReasonCodes />,
});

function ReasonCodes() {
  const entryQ = useGetEntrySystemDistributionBr();

  const q = useGetReasonCodeInsightsBr({ params: { limit: 30 } });

  const rows = q.data?.data ?? [];
  const entryRows = entryQ.data?.data ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Reason Codes (Brazil)</h1>
        <p className="text-sm text-muted-foreground mt-2">
          Unified decline taxonomy across entry systems (demo scaffold).
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Entry system coverage</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {entryQ.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : entryQ.isError ? (
            <p className="text-sm text-muted-foreground">
              Failed to load entry system distribution.
            </p>
          ) : entryRows.length === 0 ? (
            <p className="text-sm text-muted-foreground">No data yet.</p>
          ) : (
            entryRows.map((r) => (
              <div
                key={r.entry_system}
                className="flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <Badge variant="secondary">{r.entry_system}</Badge>
                  <span className="text-sm text-muted-foreground">
                    approval {r.approval_rate_pct}%
                  </span>
                </div>
                <Badge variant="secondary">{r.transaction_count}</Badge>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Top standardized decline reasons</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {q.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : q.isError ? (
            <p className="text-sm text-muted-foreground">
              Failed to load reason codes.
            </p>
          ) : rows.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No data yet. Run the simulator + DLT pipeline to populate UC
              views.
            </p>
          ) : (
            rows.map((r, idx) => (
              <div
                key={`${r.entry_system}-${r.flow_type}-${r.decline_reason_standard}-${idx}`}
                className="flex items-start justify-between gap-3"
              >
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-sm">
                      {r.decline_reason_standard}
                    </span>
                    <Badge variant="outline">{r.decline_reason_group}</Badge>
                    <Badge variant="secondary">{r.entry_system}</Badge>
                    <Badge variant="secondary">{r.flow_type}</Badge>
                    {r.pct_of_declines != null ? (
                      <Badge>{r.pct_of_declines}%</Badge>
                    ) : null}
                    <Badge variant="outline">P{r.priority}</Badge>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Action: {r.recommended_action}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Est. recoverable: {r.estimated_recoverable_declines}{" "}
                    declines · ${r.estimated_recoverable_value.toFixed(2)}
                  </div>
                </div>
                <div className="flex flex-col items-end gap-1">
                  <Badge variant="secondary">{r.decline_count}</Badge>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
