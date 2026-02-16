import { createFileRoute } from "@tanstack/react-router";
import { ErrorBoundary } from "react-error-boundary";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Database,
  BarChart3,
  Zap,
  Brain,
} from "lucide-react";

export const Route = createFileRoute("/_sidebar/about")({
  component: () => (
    <ErrorBoundary fallback={<div className="p-8 text-center text-muted-foreground">Something went wrong. Please refresh.</div>}>
      <About />
    </ErrorBoundary>
  ),
});

/* ---------- Data ---------- */

const HERO = {
  headline: "Payment Approval Rate Optimization",
  subline:
    "A unified, AI-powered platform built entirely on Databricks that accelerates payment approval rates, recovers lost revenue from false declines, and optimizes routing and retry strategies across all channels for Getnet. Features a closed-loop DecisionEngine with parallel ML + Vector Search enrichment, streaming features, agent write-back, and real-time executive dashboards.",
  kpis: [
    { label: "AI Agents", value: "8", detail: "2 Genie, 3 Model Serving, 2 AI Gateway, 1 Custom" },
    { label: "ML Models", value: "4", detail: "Approval, Risk, Routing, Retry" },
    { label: "Dashboards", value: "3", detail: "Unified AI/BI Lakeview (13 pages)" },
    { label: "Gold Views", value: "26", detail: "Real-time streaming + analytics" },
  ],
};

const SOLUTION_OVERVIEW = {
  title: "What We Built",
  intro:
    "An end-to-end platform on Databricks that unifies data, intelligence, and decision-making into a single control center. Every component is purpose-built around one goal: accelerate payment approval rates for Getnet.",
  layers: [
    {
      icon: Database,
      label: "Data Foundation",
      title: "Real-time medallion architecture (Bronze → Silver → Gold)",
      description:
        "All payment transaction data flows through Bronze (raw ingestion), Silver (enriched and validated), and Gold (business-ready views and aggregates) layers in under 5 seconds. Continuous serverless Lakeflow pipelines and Delta Live Tables ensure every dashboard, model, and agent sees the same clean, governed, up-to-date data through Unity Catalog.",
      tech: ["Lakeflow", "Delta Live Tables", "Unity Catalog", "Delta Lake", "Serverless SQL"],
    },
    {
      icon: Brain,
      label: "Intelligence Layer",
      title: "4 ML models + 8 AI agents + Vector Search",
      description:
        "Four HistGradientBoosting ML models predict approval probability, fraud risk, optimal routing, and retry success using 14 engineered features. Eight AI agents (2 Genie spaces, 3 Model Serving endpoints, 2 AI Gateway, 1 ResponsesAgent with UC tools) provide natural-language analytics, recommendations, and write-back to Lakebase. Vector Search finds similar historical transactions for experience replay.",
      tech: ["MLflow", "Model Serving", "Responses Agent", "UC Functions", "Vector Search", "Lakebase"],
    },
    {
      icon: Zap,
      label: "Decision Layer",
      title: "Closed-loop decisioning engine with parallel enrichment",
      description:
        "A unified DecisionEngine combines ML predictions, configurable business rules, agent recommendations, Vector Search similarity, and streaming real-time features into a single decision per transaction. ML and Vector Search run in parallel with thread-safe caching. Outcomes are recorded via POST /api/decision/outcome closing the feedback loop for continuous improvement.",
      tech: ["FastAPI", "Rules Engine", "Lakebase", "A/B Experiments", "Feedback Loop", "Streaming Features"],
    },
    {
      icon: BarChart3,
      label: "Analytics & Control",
      title: "AI/BI dashboards, Genie, and full-stack control panel",
      description:
        "Three unified AI/BI Lakeview dashboards (13 pages total) with embeddable analytics covering Executive & Trends, ML & Optimization, and Data & Quality. The Databricks App control center features Command Center KPIs, Smart Checkout, Decisioning, Reason Codes, Smart Retry, and two floating AI chat dialogs (Orchestrator Agent + Genie Assistant).",
      tech: ["AI/BI Dashboards", "Databricks App", "Genie Space", "React + FastAPI"],
    },
  ],
};

const TECH_SUMMARY = [
  { label: "Data Platform", value: "Databricks (Lakeflow, Delta Live Tables, Unity Catalog, Delta Lake)" },
  { label: "AI & ML", value: "MLflow, 4 Model Serving endpoints, 14-feature HistGradientBoosting models, Vector Search" },
  { label: "AI Agents", value: "8 agents (2 Genie, 3 Model Serving, 2 AI Gateway, 1 Responses Agent with 10 UC tools)" },
  { label: "LLM Strategy", value: "Claude Opus 4.6 (orchestrator / fallback) + Claude Sonnet 4.5 (Genie / specialists)" },
  { label: "Database", value: "Lakebase (managed PostgreSQL) for rules, experiments, incidents, decisions, proposals" },
  { label: "Application", value: "Databricks App: FastAPI backend + React frontend with 2 floating AI chat dialogs" },
  { label: "Dashboards", value: "3 unified AI/BI Lakeview dashboards (13 pages) + 26 gold views" },
  { label: "Decision Engine", value: "Parallel ML + VS enrichment, streaming features, thread-safe caching, outcome feedback loop" },
  { label: "Infrastructure", value: "100% serverless compute — deployed via Databricks Asset Bundles (IaC)" },
];

/* ---------- Component ---------- */

function About() {
  return (
    <div className="space-y-8 max-w-5xl">
      {/* Hero */}
      <section className="rounded-xl bg-gradient-to-br from-primary/90 to-primary px-6 py-8 text-primary-foreground">
        <Badge variant="secondary" className="mb-3 bg-white/20 text-white border-white/30 hover:bg-white/30">
          Getnet Payment Analytics
        </Badge>
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
          {HERO.headline}
        </h1>
        <p className="mt-3 text-sm md:text-base opacity-90 max-w-3xl leading-relaxed">
          {HERO.subline}
        </p>
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          {HERO.kpis.map((kpi) => (
            <div
              key={kpi.label}
              className="rounded-lg bg-white/10 backdrop-blur-sm px-4 py-3 text-center border border-white/10"
            >
              <p className="text-2xl md:text-3xl font-bold">{kpi.value}</p>
              <p className="text-xs font-medium mt-0.5 opacity-90">{kpi.label}</p>
              <p className="text-[10px] opacity-70 mt-0.5">{kpi.detail}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Solution Overview */}
      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold tracking-tight">{SOLUTION_OVERVIEW.title}</h2>
          <p className="text-sm text-muted-foreground mt-1 max-w-3xl">
            {SOLUTION_OVERVIEW.intro}
          </p>
        </div>
        <div className="space-y-3">
          {SOLUTION_OVERVIEW.layers.map((layer, i) => {
            const Icon = layer.icon;
            return (
              <Card key={layer.label} className="glass-card border border-border/80 overflow-hidden">
                <CardContent className="flex gap-4 pt-5">
                  <div className="flex flex-col items-center gap-1 pt-0.5">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-sm">
                      {i + 1}
                    </div>
                    {i < SOLUTION_OVERVIEW.layers.length - 1 && (
                      <div className="w-px flex-1 bg-border" />
                    )}
                  </div>
                  <div className="flex-1 pb-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Badge variant="outline" className="text-xs gap-1">
                        <Icon className="h-3 w-3" />
                        {layer.label}
                      </Badge>
                    </div>
                    <p className="text-sm font-semibold mt-2">{layer.title}</p>
                    <p className="text-xs text-muted-foreground mt-1 leading-relaxed max-w-2xl">
                      {layer.description}
                    </p>
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {layer.tech.map((t) => (
                        <Badge key={t} variant="secondary" className="text-[10px] font-normal">
                          {t}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      <Separator />

      {/* Technology Summary */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold tracking-tight">Technology at a Glance</h2>
        <Card className="glass-card border border-border/80">
          <CardContent className="pt-5">
            <div className="grid gap-3 sm:grid-cols-2">
              {TECH_SUMMARY.map((item) => (
                <div key={item.label} className="flex gap-2">
                  <span className="text-xs font-semibold text-foreground whitespace-nowrap min-w-[120px]">
                    {item.label}
                  </span>
                  <span className="text-xs text-muted-foreground">{item.value}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
