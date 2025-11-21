/**
 * Frontend Dashboard 메인 App 컴포넌트
 * 
 * 연금 감성 분석 플랫폼의 대시보드 UI입니다.
 * 라우팅, 상태 관리, 전역 컴포넌트를 설정합니다.
 */

import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { SidebarProvider } from "@/components/ui/sidebar";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Routes, Route } from "react-router-dom";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { Header } from "@/components/layout/Header";
import MemoPad from "@/components/MemoPad";

// 페이지 컴포넌트 import
import Index from "./pages/Index";  // 메인 대시보드
import Analytics from "./pages/Analytics";  // 분석 페이지
import Explore from "./pages/Explore";  // 탐색 페이지
import Events from "./pages/Events";  // 이벤트 페이지
import Monitoring from "./pages/Monitoring";  // 모니터링 페이지
import Alerts from "./pages/Alerts";  // 알림 페이지
import Users from "./pages/Users";  // 사용자 관리
import Settings from "./pages/Settings";  // 설정 페이지
import Help from "./pages/Help";  // 도움말 페이지
import NotFound from "./pages/NotFound";  // 404 페이지
import Services from "./pages/Services";  // 서비스 현황
import Mesh from "./pages/Mesh";  // 서비스 메시

// React Query 클라이언트 인스턴스 생성
const queryClient = new QueryClient();

/**
 * App 컴포넌트
 * 
 * 전체 애플리케이션의 루트 컴포넌트입니다.
 * 필요한 Provider들을 설정하고 라우팅 규칙을 정의합니다.
 */
const App = () => (
  <QueryClientProvider client={queryClient}> {/* React Query를 위한 Provider */}
    <TooltipProvider> {/* 툴팁 기능 Provider */}
      <Toaster /> {/* 토스트 알림 컴포넌트 */}
      <Sonner /> {/* Sonner 토스트 알림 컴포넌트 */}
      <SidebarProvider> {/* 사이드바 상태 관리 Provider */}
        <div className="min-h-screen flex w-full bg-background">
          <AppSidebar /> {/* 사이드바 네비게이션 */}
          <div className="flex-1 flex flex-col">
            <Header /> {/* 헤더 컴포넌트 */}
            <main className="flex-1">
              {/* Global floating memo pad */}
              <MemoPad />
              <Routes> {/* 라우팅 설정 */}
                {/* 메인 대시보드 */}
                <Route path="/" element={<Index />} />
                
                {/* 주요 기능 페이지 */}
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/explore" element={<Explore />} />
                <Route path="/events" element={<Events />} />
                <Route path="/monitoring" element={<Monitoring />} />
                <Route path="/alerts" element={<Alerts />} />
                
                {/* 관리 페이지 */}
                <Route path="/users" element={<Users />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/help" element={<Help />} />
                
                {/* 서비스 관련 페이지 */}
                <Route path="/services" element={<Services />} />
                <Route path="/mesh" element={<Mesh />} />
                
                {/* 모든 커스텀 라우트는 catch-all "*" 라우트 위에 추가 */}
                <Route path="*" element={<NotFound />} /> {/* 404 페이지 */}
              </Routes>
            </main>
          </div>
        </div>
      </SidebarProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
