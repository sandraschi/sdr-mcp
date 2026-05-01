import * as Tooltip from "@radix-ui/react-tooltip";
import {
  Activity,
  BookOpen,
  Grid3X3,
  HelpCircle,
  LayoutDashboard,
  type LucideIcon,
  MessageSquare,
  Radio,
  Settings,
  Waves,
  Wrench,
} from "lucide-react";
import { NavLink } from "react-router-dom";

interface NavItem {
  label: string;
  icon: LucideIcon;
  path: string;
}

const navItems: NavItem[] = [
  { label: "Overview", icon: LayoutDashboard, path: "/" },
  { label: "Spectrum", icon: Radio, path: "/spectrum" },
  { label: "Waterfall", icon: Waves, path: "/waterfall" },
  { label: "Stations", icon: BookOpen, path: "/stations" },
  { label: "Tools", icon: Wrench, path: "/tools" },
  { label: "Status", icon: Activity, path: "/status" },
  { label: "App Hub", icon: Grid3X3, path: "/apps" },
  { label: "AI Command", icon: MessageSquare, path: "/chat" },
  { label: "Help", icon: HelpCircle, path: "/help" },
  { label: "Settings", icon: Settings, path: "/settings" },
];

interface SidebarProps {
  collapsed: boolean;
}

export function Sidebar({ collapsed }: SidebarProps) {
  return (
    <aside
      className={`border-r border-slate-800 bg-slate-950/80 flex flex-col transition-all duration-300 ${
        collapsed ? "w-16" : "w-56"
      }`}
    >
      <div className="flex items-center h-14 border-b border-slate-800 px-4">
        {!collapsed && (
          <span className="text-sm font-semibold text-white tracking-wide">
            SDR MCP
          </span>
        )}
        {collapsed && (
          <span className="text-sm font-bold text-white mx-auto">S</span>
        )}
      </div>

      <nav className="flex-1 py-4 space-y-1 px-2">
        {navItems.map((item) =>
          collapsed ? (
            <Tooltip.Root key={item.path}>
              <Tooltip.Trigger asChild>
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center justify-center h-10 w-10 mx-auto rounded-md transition-colors ${
                      isActive
                        ? "bg-blue-600/20 text-blue-400"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                    }`
                  }
                >
                  <item.icon className="h-4 w-4" />
                </NavLink>
              </Tooltip.Trigger>
              <Tooltip.Portal>
                <Tooltip.Content
                  side="right"
                  className="bg-slate-900 text-slate-200 text-xs px-2 py-1 rounded border border-slate-700"
                >
                  {item.label}
                </Tooltip.Content>
              </Tooltip.Portal>
            </Tooltip.Root>
          ) : (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive
                    ? "bg-blue-600/20 text-blue-400"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`
              }
            >
              <item.icon className="h-4 w-4 shrink-0" />
              <span>{item.label}</span>
            </NavLink>
          ),
        )}
      </nav>
    </aside>
  );
}
