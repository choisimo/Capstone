/**
 * 대시보드 페이지 컴포넌트
 * 
 * 연금 감성 분석 플랫폼의 메인 대시보드입니다.
 * 실시간 여론 현황, 주요 지표, 트렌드 차트 등을 표시합니다.
 */

import { Activity, Users, TrendingUp, AlertTriangle, MessageSquare } from "lucide-react";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { SentimentChart } from "@/components/dashboard/SentimentChart";
import { TrendChart } from "@/components/dashboard/TrendChart";
import { IssueCard } from "@/components/dashboard/IssueCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

// 모의 이슈 데이터 (실제로는 API에서 가져옴)
const mockIssues = [
  {
    title: "보험료율 13% 인상 정책에 대한 시민 반응",
    sentiment: "negative" as const,  // 부정적 감성
    mentions: 1247,  // 언급 횟수
    trend: "up" as const,  // 상승 트렌드
    category: "보험료"  // 카테고리
  },
  {
    title: "국민연금 수급연령 상향 조정 논의",
    sentiment: "negative" as const,
    mentions: 892,
    trend: "up" as const,
    category: "수급연령"
  },
  {
    title: "청년층 국민연금 가입률 증가 호조",
    sentiment: "positive" as const,
    mentions: 534,
    trend: "up" as const,
    category: "가입률"
  },
  {
    title: "연금개혁 TF 구성 발표",
    sentiment: "neutral" as const,
    mentions: 423,
    trend: "stable" as const,
    category: "정책"
  }
];

/**
 * Dashboard 컴포넌트
 * 
 * 메인 대시보드 UI를 렌더링합니다.
 * 주요 지표, 차트, 이슈 카드 등을 포함합니다.
 */
export default function Dashboard() {
  return (
    <div className="p-6 space-y-6">
      {/* 헤더 섹션 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">여론 분석 대시보드</h1>
          <p className="text-muted-foreground">국민연금 정책에 대한 실시간 여론 현황</p>
        </div>
        <div className="flex gap-2">
          {/* 액션 버튼 */}
          <Button variant="outline" size="sm">
            리포트 다운로드
          </Button>
          <Button size="sm">
            실시간 새로고침
          </Button>
        </div>
      </div>

      {/* 주요 지표 카드 섹션 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* 전체 언급량 지표 */}
        <MetricCard
          title="전체 언급량"
          value="12,547"
          change="+8.2% 전일 대비"
          changeType="positive"
          icon={<MessageSquare className="h-4 w-4" />}
        />
        {/* 긍정 감성 비율 */}
        <MetricCard
          title="긍정 감정"
          value="42%"
          change="-2.1% 전일 대비"
          changeType="negative"
          icon={<TrendingUp className="h-4 w-4" />}
        />
        {/* 부정 감성 비율 */}
        <MetricCard
          title="부정 감정"
          value="23%"
          change="+5.3% 전일 대비"
          changeType="negative"
          icon={<TrendingUp className="h-4 w-4" />}
        />
        {/* 활성 이슈 수 */}
        <MetricCard
          title="활성 이슈"
          value="18"
          change="+3 신규"
          changeType="positive"
          icon={<Activity className="h-4 w-4" />}
        />
        {/* 경보 상태 */}
        <MetricCard
          title="경보 상태"
          value="3"
          change="주의 2건, 경고 1건"
          changeType="negative"
          icon={<AlertTriangle className="h-4 w-4" />}
        />
      </div>

      {/* 차트 섹션 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <SentimentChart />  {/* 감성 분석 차트 */}
        <TrendChart />
      </div>

      {/* Top Issues */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg font-semibold">주요 이슈 Top 4</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {mockIssues.map((issue, index) => (
                  <IssueCard key={index} {...issue} />
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg font-semibold">채널별 활동</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">네이버 뉴스</span>
                <span className="text-sm text-muted-foreground">4,234 언급</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div className="bg-primary h-2 rounded-full" style={{ width: "65%" }}></div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">커뮤니티</span>
                <span className="text-sm text-muted-foreground">3,127 언급</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div className="bg-primary h-2 rounded-full" style={{ width: "48%" }}></div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">소셜미디어</span>
                <span className="text-sm text-muted-foreground">2,891 언급</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div className="bg-primary h-2 rounded-full" style={{ width: "44%" }}></div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">온라인 미디어</span>
                <span className="text-sm text-muted-foreground">2,295 언급</span>
              </div>
              <div className="w-full bg-muted rounded-full h-2">
                <div className="bg-primary h-2 rounded-full" style={{ width: "35%" }}></div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}