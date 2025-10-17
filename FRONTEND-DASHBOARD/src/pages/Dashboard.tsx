/**
 * 대시보드 페이지 컴포넌트
 * 
 * 연금 감성 분석 플랫폼의 메인 대시보드입니다.
 * 실시간 여론 현황, 주요 지표, 트렌드 차트 등을 표시합니다.
 */

import { useEffect, useState } from "react";
import { Activity, TrendingUp, AlertTriangle, MessageSquare, RefreshCw } from "lucide-react";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { SentimentChart } from "@/components/dashboard/SentimentChart";
import { TrendChart } from "@/components/dashboard/TrendChart";
import { IssueCard } from "@/components/dashboard/IssueCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  DashboardOverview,
  IssueSummary,
  fetchDashboardOverview,
  fetchDashboardTopIssues,
} from "@/lib/api";

const DEFAULT_OVERVIEW: DashboardOverview = {
  total_mentions: 0,
  positive_ratio: 0,
  negative_ratio: 0,
  active_issues: 0,
  alerts: {
    warning: 0,
    critical: 0,
  },
  channels: [],
};

function toPercentLabel(value: number): string {
  if (Number.isNaN(value)) return "0%";
  const ratio = value <= 1 ? value * 100 : value;
  return `${ratio.toFixed(1)}%`;
}

function buildAlertLabel(overview: DashboardOverview): string {
  const warning = overview.alerts?.warning ?? 0;
  const critical = overview.alerts?.critical ?? 0;
  if (!warning && !critical) {
    return "정상";
  }
  return `주의 ${warning} · 경고 ${critical}`;
}

export default function Dashboard() {
  const [overview, setOverview] = useState<DashboardOverview>(DEFAULT_OVERVIEW);
  const [issues, setIssues] = useState<IssueSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);

      const [overviewData, issueData] = await Promise.all([
        fetchDashboardOverview(),
        fetchDashboardTopIssues(4),
      ]);

      setOverview(overviewData);
      setIssues(issueData);
    } catch (err) {
      console.error("Failed to load dashboard data", err);
      setError("대시보드 데이터를 불러오지 못했습니다. 나중에 다시 시도하세요.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const channelActivity = overview.channels?.slice(0, 6) ?? [];

  return (
    <div className="p-6 space-y-6">
      {/* 헤더 섹션 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">여론 분석 대시보드</h1>
          <p className="text-muted-foreground">국민연금 정책에 대한 실시간 여론 현황</p>
        </div>
        <div className="flex gap-2">
          <Button className="h-9 px-3 text-sm" onClick={() => { /* TODO: 연결된 리포트 API 연동 */ }}>
            리포트 다운로드
          </Button>
          <Button className="h-9 px-3 text-sm" onClick={loadDashboard} disabled={loading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            {loading ? "새로고침 중" : "실시간 새로고침"}
          </Button>
        </div>
      </div>

      {/* 주요 지표 카드 섹션 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* 전체 언급량 지표 */}
        <MetricCard
          title="전체 언급량"
          value={overview.total_mentions.toLocaleString()}
          icon={<MessageSquare className="h-4 w-4" />}
        />
        {/* 긍정 감성 비율 */}
        <MetricCard
          title="긍정 감정"
          value={toPercentLabel(overview.positive_ratio)}
          icon={<TrendingUp className="h-4 w-4" />}
        />
        {/* 부정 감성 비율 */}
        <MetricCard
          title="부정 감정"
          value={toPercentLabel(overview.negative_ratio)}
          icon={<TrendingUp className="h-4 w-4" />}
        />
        {/* 활성 이슈 수 */}
        <MetricCard
          title="활성 이슈"
          value={overview.active_issues.toLocaleString()}
          icon={<Activity className="h-4 w-4" />}
        />
        {/* 경보 상태 */}
        <MetricCard
          title="경보 상태"
          value={(overview.alerts.warning + overview.alerts.critical).toString()}
          change={buildAlertLabel(overview)}
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
              {issues.length === 0 ? (
                <div className="flex h-32 w-full items-center justify-center text-sm text-muted-foreground">
                  {loading ? "이슈 데이터를 불러오는 중입니다..." : "표시할 이슈가 없습니다."}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {issues.map((issue) => (
                    <IssueCard key={issue.id} {...issue} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg font-semibold">채널별 활동</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {channelActivity.length === 0 ? (
                <p className="text-sm text-muted-foreground">채널별 데이터가 아직 제공되지 않았습니다.</p>
              ) : (
                channelActivity.map((channel) => {
                  const mentions = channel.mentions ?? 0;
                  const ratio = overview.total_mentions > 0
                    ? Math.min(100, (mentions / overview.total_mentions) * 100)
                    : 0;

                  return (
                    <div key={channel.name} className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">{channel.name}</span>
                        <span className="text-sm text-muted-foreground">
                          {mentions.toLocaleString()} 언급
                        </span>
                      </div>
                      <div className="w-full bg-muted rounded-full h-2">
                        <div
                          className="bg-primary h-2 rounded-full"
                          style={{ width: `${ratio.toFixed(1)}%` }}
                        ></div>
                      </div>
                    </div>
                  );
                })
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {error && (
        <Card className="border-destructive/40 bg-destructive/10">
          <CardContent className="py-4 text-sm text-destructive">
            {error}
          </CardContent>
        </Card>
      )}
    </div>
  );
}