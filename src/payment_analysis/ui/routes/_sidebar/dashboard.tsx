import { createFileRoute } from "@tanstack/react-router";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useGetKpisSuspense } from "@/lib/api";
import selector from "@/lib/selector";
import { ExternalLink, Code2, TrendingUp, Database } from "lucide-react";

export const Route = createFileRoute("/_sidebar/dashboard")({
  component: () => <Dashboard />,
});

const openNotebook = async (notebookId: string) => {
  try {
    const response = await fetch(`/api/notebooks/notebooks/${notebookId}/url`);
    const data = await response.json();
    window.open(data.url, "_blank");
  } catch (error) {
    console.error("Failed to open notebook:", error);
  }
};

const openDashboard = () => {
  const dashboardUrl = "https://adb-984752964297111.11.azuredatabricks.net/sql/dashboards/executive_overview";
  window.open(dashboardUrl, "_blank");
};

function Dashboard() {
  const { data } = useGetKpisSuspense(selector());

  const pct = (data.approval_rate * 100).toFixed(2);

  return (
    <div className="space-y-6">
      {/* Header with Links */}
      <div>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Approval performance</h1>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={openDashboard}
            >
              <TrendingUp className="w-4 h-4 mr-2" />
              Executive Dashboard
              <ExternalLink className="w-3 h-3 ml-2" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => openNotebook("gold_views_sql")}
            >
              <Database className="w-4 h-4 mr-2" />
              SQL Views
              <ExternalLink className="w-3 h-3 ml-2" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => openNotebook("realtime_pipeline")}
            >
              <Code2 className="w-4 h-4 mr-2" />
              DLT Pipeline
              <ExternalLink className="w-3 h-3 ml-2" />
            </Button>
          </div>
        </div>
        <p className="text-sm text-muted-foreground mt-2">
          Real-time KPIs from Unity Catalog via Lakeflow streaming
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle>Total auths</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-bold">{data.total}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Approved</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-bold">{data.approved}</CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Approval rate</CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-bold">{pct}%</CardContent>
        </Card>
      </div>

    </div>
  );
}

