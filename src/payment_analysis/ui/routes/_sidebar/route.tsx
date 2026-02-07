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

  // Executive: KPI tiles + DBSQL dashboards hub (for executives and high-level storytelling)
  const executiveItems: NavItem[] = [
    { to: "/dashboard", label: "KPI overview", icon: <BarChart3 size={16} />, match: (p) => p === "/dashboard" },
    { to: "/dashboards", label: "DBSQL dashboards", icon: <LayoutDashboard size={16} />, match: (p) => p === "/dashboards" },
  ];

  // Performance & analytics: Smart Checkout + Reason Codes + Smart Retry + Declines (one approval-accelerator system)
  const performanceItems: NavItem[] = [
    { to: "/smart-checkout", label: "Smart Checkout", icon: <CreditCard size={16} />, match: (p) => p === "/smart-checkout" },
    { to: "/reason-codes", label: "Reason codes", icon: <ListChecks size={16} />, match: (p) => p === "/reason-codes" },
    { to: "/smart-retry", label: "Smart Retry", icon: <RotateCcw size={16} />, match: (p) => p === "/smart-retry" },
    { to: "/declines", label: "Declines", icon: <BadgeX size={16} />, match: (p) => p === "/declines" },
  ];

  // Genie & agents: natural language and agent interaction (analysts, PMs)
  const genieItems: NavItem[] = [
    { to: "/ai-agents", label: "AI agents", icon: <Bot size={16} />, match: (p) => p === "/ai-agents" },
    { to: "/decisioning", label: "Decisioning & Genie", icon: <MessageSquareText size={16} />, match: (p) => p === "/decisioning" },
  ];

  // Operations: setup, notebooks, models, incidents, experiments, rules
  const operationsItems: NavItem[] = [
    { to: "/setup", label: "Setup & run", icon: <Rocket size={16} />, match: (p) => p === "/setup" },
    { to: "/notebooks", label: "Notebooks", icon: <Code2 size={16} />, match: (p) => p === "/notebooks" },
    { to: "/models", label: "ML models", icon: <Brain size={16} />, match: (p) => p === "/models" },
    { to: "/incidents", label: "Incidents", icon: <AlertTriangle size={16} />, match: (p) => p === "/incidents" },
    { to: "/experiments", label: "Experiments", icon: <FlaskConical size={16} />, match: (p) => p === "/experiments" },
    { to: "/rules", label: "Rules", icon: <ScrollText size={16} />, match: (p) => p === "/rules" },
  ];

  const settingsItems: NavItem[] = [
    { to: "/profile", label: "Profile", icon: <User size={16} />, match: (p) => p === "/profile" },
  ];

  return (
    <SidebarLayout>
      <SidebarGroup>
        <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-3 py-2">
          Executive
        </SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {executiveItems.map((item) => (
              <SidebarMenuItem key={item.to}>
                <NavLink item={item} isActive={item.match(location.pathname)} />
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
      <SidebarGroup>
        <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-3 py-2">
          Performance & analytics
        </SidebarGroupLabel>
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
      <SidebarGroup>
        <SidebarGroupLabel className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-3 py-2">
          Genie & agents
        </SidebarGroupLabel>
        <SidebarGroupContent>
          <SidebarMenu>
            {genieItems.map((item) => (
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
