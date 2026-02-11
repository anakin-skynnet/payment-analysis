/** Sidebar navigation — getnet Global Payments Command Center (reference layout). */
import { createFileRoute, Link, useLocation } from "@tanstack/react-router";
import {
  BarChart3,
  BadgeX,
  Brain,
  Bot,
  Code2,
  CreditCard,
  FlaskConical,
  Gauge,
  LayoutDashboard,
  ListChecks,
  MessageSquareText,
  RotateCcw,
  ScrollText,
  Settings,
  User,
} from "lucide-react";
import SidebarLayout from "@/components/apx/sidebar-layout";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_sidebar")({
  component: () => <Layout />,
});

type NavItem = {
  to: string;
  label: string;
  icon: React.ReactNode;
  tooltip: string;
  match: (path: string) => boolean;
};

function NavLink({ item, isActive }: { item: NavItem; isActive: boolean }) {
  const link = (
    <Link
      to={item.to}
      className={cn(
        "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 min-w-0 min-h-[2.75rem]",
        "border-l-[3px] border-transparent -ml-[3px]",
        isActive
          ? "bg-sidebar-accent text-sidebar-accent-foreground border-sidebar-primary shadow-sm"
          : "text-sidebar-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground hover:border-sidebar-primary/30",
      )}
      aria-current={isActive ? "page" : undefined}
    >
      <span className="shrink-0 size-5 flex items-center justify-center [&>svg]:size-[1.125rem] text-current">{item.icon}</span>
      <span className="truncate">{item.label}</span>
    </Link>
  );
  return (
    <Tooltip>
      <TooltipTrigger asChild>{link}</TooltipTrigger>
      <TooltipContent side="right" className="max-w-[220px]">
        {item.tooltip}
      </TooltipContent>
    </Tooltip>
  );
}

function Layout() {
  const location = useLocation();

  // Reference: Overview, Real-Time Monitor, Performance, Alerts Data Quality, Settings
  const overviewItems: NavItem[] = [
    { to: "/command-center", label: "Overview", icon: <LayoutDashboard size={16} />, tooltip: "Main hub: KPIs, embedded dashboard, alerts, control panel, and AI chat.", match: (p) => p === "/command-center" },
    { to: "/about", label: "About this platform", icon: <ScrollText size={16} />, tooltip: "What this platform does and how it helps optimize payment approval rates.", match: (p) => p === "/about" },
  ];

  const realTimeItems: NavItem[] = [
    { to: "/incidents", label: "Real-Time Monitor", icon: <BarChart3 size={16} />, tooltip: "Live payment volume, incidents, and last-hour metrics per second.", match: (p) => p === "/incidents" },
  ];

  const performanceItems: NavItem[] = [
    { to: "/dashboard", label: "Executive overview", icon: <BarChart3 size={16} />, tooltip: "High-level KPIs, approval trends, and solution performance at a glance.", match: (p) => p === "/dashboard" },
    { to: "/dashboards", label: "Dashboards", icon: <LayoutDashboard size={16} />, tooltip: "All BI dashboards: executive, declines, real-time, fraud, routing, and more.", match: (p) => p === "/dashboards" },
    { to: "/declines", label: "Declines", icon: <BadgeX size={16} />, tooltip: "Analyze decline reasons, recovery opportunities, and recommended actions.", match: (p) => p === "/declines" },
    { to: "/reason-codes", label: "Reason Codes", icon: <ListChecks size={16} />, tooltip: "Reason-code taxonomy, insights, and estimated recoverable value.", match: (p) => p === "/reason-codes" },
  ];

  const alertsDataQualityItems: NavItem[] = [
    { to: "/alerts-data-quality", label: "Alerts & Data Quality", icon: <Gauge size={16} />, tooltip: "Active alerts, data quality metrics, and streaming health.", match: (p) => p === "/alerts-data-quality" },
  ];

  const settingsItems: NavItem[] = [
    { to: "/profile", label: "Profile", icon: <User size={16} />, tooltip: "User settings and CCO login.", match: (p) => p === "/profile" },
    { to: "/setup", label: "Control panel", icon: <Settings size={16} />, tooltip: "Configure catalog, schema, and run setup jobs or pipelines.", match: (p) => p === "/setup" },
  ];

  // More: initiatives, AI, operations (still accessible)
  const moreItems: NavItem[] = [
    { to: "/initiatives", label: "Payment Services & Data", icon: <LayoutDashboard size={16} />, tooltip: "Payment services and data sources overview.", match: (p) => p === "/initiatives" },
    { to: "/decisioning", label: "Recommendations & decisions", icon: <MessageSquareText size={16} />, tooltip: "Decisioning API and recommended actions for approvals.", match: (p) => p === "/decisioning" },
    { to: "/rules", label: "Rules", icon: <ScrollText size={16} />, tooltip: "Approval and routing rules configuration.", match: (p) => p === "/rules" },
    { to: "/smart-checkout", label: "Smart Checkout", icon: <CreditCard size={16} />, tooltip: "Smart Checkout and payment-link performance by path.", match: (p) => p === "/smart-checkout" },
    { to: "/smart-retry", label: "Smart Retry", icon: <RotateCcw size={16} />, tooltip: "Retry strategy performance and recovery by scenario.", match: (p) => p === "/smart-retry" },
    { to: "/ai-agents", label: "AI agents", icon: <Bot size={16} />, tooltip: "AgentBricks agents: orchestrator and specialists (routing, retry, decline, risk, performance).", match: (p) => p === "/ai-agents" },
    { to: "/notebooks", label: "Notebooks", icon: <Code2 size={16} />, tooltip: "Databricks notebooks for ETL, streaming, and gold views.", match: (p) => p === "/notebooks" },
    { to: "/models", label: "ML models", icon: <Brain size={16} />, tooltip: "ML models for approval, risk, routing, and retry (Unity Catalog).", match: (p) => p === "/models" },
    { to: "/experiments", label: "Experiments", icon: <FlaskConical size={16} />, tooltip: "MLflow experiments and runs.", match: (p) => p === "/experiments" },
  ];

  return (
    <SidebarLayout>
      <nav aria-label="Primary navigation" className="contents">
        <SidebarGroup aria-label="Overview">
          <SidebarGroupLabel className="nav-group-label">Overview</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {overviewItems.map((item) => (
                <SidebarMenuItem key={item.to}>
                  <NavLink item={item} isActive={item.match(location.pathname)} />
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup aria-label="Real-Time Monitor">
          <SidebarGroupLabel className="nav-group-label">Real-Time Monitor</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {realTimeItems.map((item) => (
                <SidebarMenuItem key={item.to}>
                  <NavLink item={item} isActive={item.match(location.pathname)} />
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup aria-label="Performance">
          <SidebarGroupLabel className="nav-group-label">Performance</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {performanceItems.map((item) => (
                <SidebarMenuItem key={item.to}>
                  <NavLink item={item} isActive={item.match(location.pathname)} />
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup aria-label="Alerts Data Quality">
          <SidebarGroupLabel className="nav-group-label">Alerts & Data Quality</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {alertsDataQualityItems.map((item) => (
                <SidebarMenuItem key={item.to}>
                  <NavLink item={item} isActive={item.match(location.pathname)} />
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup aria-label="Settings">
          <SidebarGroupLabel className="nav-group-label">Settings</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {settingsItems.map((item) => (
                <SidebarMenuItem key={item.to}>
                  <NavLink item={item} isActive={item.match(location.pathname)} />
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup aria-label="More">
          <SidebarGroupLabel className="nav-group-label">More</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {moreItems.map((item) => (
                <SidebarMenuItem key={item.to}>
                  <NavLink item={item} isActive={item.match(location.pathname)} />
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </nav>
    </SidebarLayout>
  );
}
