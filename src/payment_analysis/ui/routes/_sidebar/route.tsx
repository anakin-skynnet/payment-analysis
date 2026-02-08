import SidebarLayout from "@/components/apx/sidebar-layout";
import { createFileRoute, Link, useLocation } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import {
  AlertTriangle,
  BarChart3,
  BadgeX,
  FlaskConical,
  User,
  LayoutDashboard,
  Code2,
  Brain,
  Bot,
  Rocket,
  CreditCard,
  ListChecks,
  RotateCcw,
  ScrollText,
  MessageSquareText,
} from "lucide-react";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

export const Route = createFileRoute("/_sidebar")({
  component: () => <Layout />,
});

type NavItem = {
  to: string;
  label: string;
  icon: React.ReactNode;
  match: (path: string) => boolean;
};

function NavLink({ item, isActive }: { item: NavItem; isActive: boolean }) {
  return (
    <Link
      to={item.to}
      className={cn(
        "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-200",
        "border-l-2 border-transparent -ml-[2px]",
        isActive
          ? "bg-sidebar-accent text-sidebar-accent-foreground border-sidebar-primary"
          : "text-sidebar-foreground hover:bg-sidebar-accent/70 hover:text-sidebar-accent-foreground",
      )}
    >
      {item.icon}
      <span>{item.label}</span>
    </Link>
  );
}

function Layout() {
  const location = useLocation();

  // Overview: single place for KPIs and deep-dive dashboards (CEO-friendly)
  const overviewItems: NavItem[] = [
    { to: "/dashboard", label: "KPI overview", icon: <BarChart3 size={16} />, match: (p) => p === "/dashboard" },
    { to: "/dashboards", label: "Dashboards", icon: <LayoutDashboard size={16} />, match: (p) => p === "/dashboards" },
  ];

  // Initiatives: Smart Checkout, Reason Codes, Smart Retry (Getnet business objectives)
  const initiativeItems: NavItem[] = [
    { to: "/smart-checkout", label: "Smart Checkout", icon: <CreditCard size={16} />, match: (p) => p === "/smart-checkout" },
    { to: "/reason-codes", label: "Reason Codes", icon: <ListChecks size={16} />, match: (p) => p === "/reason-codes" },
    { to: "/smart-retry", label: "Smart Retry", icon: <RotateCcw size={16} />, match: (p) => p === "/smart-retry" },
    { to: "/declines", label: "Declines & insights", icon: <BadgeX size={16} />, match: (p) => p === "/declines" },
  ];

  // AI & decisioning: Genie and agent-driven recommendations
  const decisioningItems: NavItem[] = [
    { to: "/decisioning", label: "Decisioning & Genie", icon: <MessageSquareText size={16} />, match: (p) => p === "/decisioning" },
    { to: "/ai-agents", label: "AI agents", icon: <Bot size={16} />, match: (p) => p === "/ai-agents" },
  ];

  // Operations: setup, notebooks, models, incidents, experiments, rules
  const operationsItems: NavItem[] = [
    { to: "/setup", label: "Setup & run", icon: <Rocket size={16} />, match: (p) => p === "/setup" },
    { to: "/notebooks", label: "Notebooks", icon: <Code2 size={16} />, match: (p) => p === "/notebooks" },
    { to: "/models", label: "ML models", icon: <Brain size={16} />, match: (p) => p === "/models" },
    { to: "/rules", label: "Rules", icon: <ScrollText size={16} />, match: (p) => p === "/rules" },
    { to: "/incidents", label: "Incidents", icon: <AlertTriangle size={16} />, match: (p) => p === "/incidents" },
    { to: "/experiments", label: "Experiments", icon: <FlaskConical size={16} />, match: (p) => p === "/experiments" },
  ];

  const settingsItems: NavItem[] = [
    { to: "/profile", label: "Profile", icon: <User size={16} />, match: (p) => p === "/profile" },
  ];

  return (
    <SidebarLayout>
      <SidebarGroup>
        <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-3 py-2">
          Overview
        </SidebarGroupLabel>
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
      <SidebarGroup>
        <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-3 py-2">
          Initiatives
        </SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {initiativeItems.map((item) => (
              <SidebarMenuItem key={item.to}>
                <NavLink item={item} isActive={item.match(location.pathname)} />
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
      <SidebarGroup>
        <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-3 py-2">
          AI & decisioning
        </SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {decisioningItems.map((item) => (
              <SidebarMenuItem key={item.to}>
                <NavLink item={item} isActive={item.match(location.pathname)} />
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
      <SidebarGroup>
        <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-3 py-2">
          Operations
        </SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {operationsItems.map((item) => (
              <SidebarMenuItem key={item.to}>
                <NavLink item={item} isActive={item.match(location.pathname)} />
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
      <SidebarGroup>
        <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-3 py-2">
          Settings
        </SidebarGroupLabel>
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
    </SidebarLayout>
  );
}
