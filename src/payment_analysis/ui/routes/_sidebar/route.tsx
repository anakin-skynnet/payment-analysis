import SidebarLayout from "@/components/apx/sidebar-layout";
import { createFileRoute, Link, useLocation } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import {
  AlertTriangle,
  BarChart3,
  BadgeX,
  FlaskConical,
  User,
  Wand2,
  LayoutDashboard,
  Code2,
  Brain,
  Bot,
  Rocket,
  CreditCard,
  ListChecks,
  RotateCcw,
  ScrollText,
} from "lucide-react";
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

export const Route = createFileRoute("/_sidebar")({
  component: () => <Layout />,
});

function Layout() {
  const location = useLocation();

  const navItems = [
    {
      to: "/dashboard",
      label: "Dashboard",
      icon: <BarChart3 size={16} />,
      match: (path: string) => path === "/dashboard",
    },
    {
      to: "/setup",
      label: "Setup & Run",
      icon: <Rocket size={16} />,
      match: (path: string) => path === "/setup",
    },
    {
      to: "/dashboards",
      label: "Analytics Dashboards",
      icon: <LayoutDashboard size={16} />,
      match: (path: string) => path === "/dashboards",
    },
    {
      to: "/notebooks",
      label: "Notebooks",
      icon: <Code2 size={16} />,
      match: (path: string) => path === "/notebooks",
    },
    {
      to: "/models",
      label: "ML Models",
      icon: <Brain size={16} />,
      match: (path: string) => path === "/models",
    },
    {
      to: "/ai-agents",
      label: "AI Agents",
      icon: <Bot size={16} />,
      match: (path: string) => path === "/ai-agents",
    },
    {
      to: "/decisioning",
      label: "Decisioning",
      icon: <Wand2 size={16} />,
      match: (path: string) => path === "/decisioning",
    },
    {
      to: "/rules",
      label: "Rules",
      icon: <ScrollText size={16} />,
      match: (path: string) => path === "/rules",
    },
    {
      to: "/experiments",
      label: "Experiments",
      icon: <FlaskConical size={16} />,
      match: (path: string) => path === "/experiments",
    },
    {
      to: "/incidents",
      label: "Incidents",
      icon: <AlertTriangle size={16} />,
      match: (path: string) => path === "/incidents",
    },
    {
      to: "/declines",
      label: "Declines",
      icon: <BadgeX size={16} />,
      match: (path: string) => path === "/declines",
    },
    {
      to: "/smart-checkout",
      label: "Smart Checkout",
      icon: <CreditCard size={16} />,
      match: (path: string) => path === "/smart-checkout",
    },
    {
      to: "/reason-codes",
      label: "Reason Codes",
      icon: <ListChecks size={16} />,
      match: (path: string) => path === "/reason-codes",
    },
    {
      to: "/smart-retry",
      label: "Smart Retry",
      icon: <RotateCcw size={16} />,
      match: (path: string) => path === "/smart-retry",
    },
    {
      to: "/profile",
      label: "Profile",
      icon: <User size={16} />,
      match: (path: string) => path === "/profile",
    },
  ];

  return (
    <SidebarLayout>
      <SidebarGroup>
        <SidebarGroupContent>
          <SidebarMenu>
            {navItems.map((item) => {
              const isActive = item.match(location.pathname);
              return (
                <SidebarMenuItem key={item.to}>
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
                </SidebarMenuItem>
              );
            })}
          </SidebarMenu>
        </SidebarGroupContent>
      </SidebarGroup>
    </SidebarLayout>
  );
}
