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
import { cn } from "@/lib/utils";

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
}

function Layout() {
  const location = useLocation();

  // Reference: Overview, Real-Time Monitor, Performance, Alerts Data Quality, Settings
  const overviewItems: NavItem[] = [
    { to: "/command-center", label: "Overview", icon: <LayoutDashboard size={16} />, match: (p) => p === "/command-center" },
    { to: "/about", label: "About this platform", icon: <ScrollText size={16} />, match: (p) => p === "/about" },
  ];

  const realTimeItems: NavItem[] = [
    { to: "/incidents", label: "Real-Time Monitor", icon: <BarChart3 size={16} />, match: (p) => p === "/incidents" },
  ];

  const performanceItems: NavItem[] = [
    { to: "/dashboard", label: "Executive overview", icon: <BarChart3 size={16} />, match: (p) => p === "/dashboard" },
    { to: "/dashboards", label: "Dashboards", icon: <LayoutDashboard size={16} />, match: (p) => p === "/dashboards" },
    { to: "/declines", label: "Declines", icon: <BadgeX size={16} />, match: (p) => p === "/declines" },
    { to: "/reason-codes", label: "Reason Codes", icon: <ListChecks size={16} />, match: (p) => p === "/reason-codes" },
  ];

  const alertsDataQualityItems: NavItem[] = [
    { to: "/alerts-data-quality", label: "Alerts & Data Quality", icon: <Gauge size={16} />, match: (p) => p === "/alerts-data-quality" },
  ];

  const settingsItems: NavItem[] = [
    { to: "/profile", label: "Profile", icon: <User size={16} />, match: (p) => p === "/profile" },
    { to: "/setup", label: "Control panel", icon: <Settings size={16} />, match: (p) => p === "/setup" },
  ];

  // More: initiatives, AI, operations (still accessible)
  const moreItems: NavItem[] = [
    { to: "/initiatives", label: "Payment Services & Data", icon: <LayoutDashboard size={16} />, match: (p) => p === "/initiatives" },
    { to: "/decisioning", label: "Recommendations & decisions", icon: <MessageSquareText size={16} />, match: (p) => p === "/decisioning" },
    { to: "/rules", label: "Rules", icon: <ScrollText size={16} />, match: (p) => p === "/rules" },
    { to: "/smart-checkout", label: "Smart Checkout", icon: <CreditCard size={16} />, match: (p) => p === "/smart-checkout" },
    { to: "/smart-retry", label: "Smart Retry", icon: <RotateCcw size={16} />, match: (p) => p === "/smart-retry" },
    { to: "/ai-agents", label: "AI agents", icon: <Bot size={16} />, match: (p) => p === "/ai-agents" },
    { to: "/notebooks", label: "Notebooks", icon: <Code2 size={16} />, match: (p) => p === "/notebooks" },
    { to: "/models", label: "ML models", icon: <Brain size={16} />, match: (p) => p === "/models" },
    { to: "/experiments", label: "Experiments", icon: <FlaskConical size={16} />, match: (p) => p === "/experiments" },
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
