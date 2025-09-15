import { NavLink, useLocation } from "react-router-dom";
import {
  BarChart3,
  Search,
  TrendingUp,
  Bell,
  Settings,
  HelpCircle,
  Users,
  Activity,
  Layers
 } from "lucide-react";


import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";

const navigationItems = [
  { 
    title: "홈 대시보드", 
    url: "/", 
    icon: () => <img src="/nps-preview-favicon.png" alt="Home" className="h-4 w-4" />
  },
  { title: "분석 대시보드", url: "/analytics", icon: BarChart3 },
  { title: "이슈 탐색", url: "/explore", icon: Search },
  { title: "이벤트 분석", url: "/events", icon: TrendingUp },
  { title: "실시간 모니터링", url: "/monitoring", icon: Activity },
  { title: "서비스", url: "/services", icon: Layers },
];

const managementItems = [
  { title: "알림 센터", url: "/alerts", icon: Bell },
  { title: "사용자 관리", url: "/users", icon: Users },
  { title: "설정", url: "/settings", icon: Settings },
  { title: "도움말", url: "/help", icon: HelpCircle },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const location = useLocation();
  const isCollapsed = state === "collapsed";

  const isActive = (path: string) => {
    if (path === "/") {
      return location.pathname === "/";
    }
    return location.pathname.startsWith(path);
  };

  const getNavClassName = (path: string) => {
    const baseClasses = "w-full justify-start font-medium transition-colors";
    if (isActive(path)) {
      return `${baseClasses} bg-primary text-primary-foreground`;
    }
    return `${baseClasses} hover:bg-accent hover:text-accent-foreground`;
  };

  return (
    <Sidebar className={isCollapsed ? "w-14" : "w-64"} collapsible="icon">
      <SidebarHeader className="border-b border-border p-4">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary">
            <BarChart3 className="h-4 w-4 text-primary-foreground" />
          </div>
          {!isCollapsed && (
            <div>
              <h2 className="text-sm font-semibold text-foreground">국민연금</h2>
              <p className="text-xs text-muted-foreground">여론분석 시스템</p>
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>주요 기능</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navigationItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink to={item.url} className={getNavClassName(item.url)}>
                      <item.icon className="h-4 w-4" />
                      {!isCollapsed && <span>{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>관리</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {managementItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <NavLink to={item.url} className={getNavClassName(item.url)}>
                      <item.icon className="h-4 w-4" />
                      {!isCollapsed && <span>{item.title}</span>}
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}