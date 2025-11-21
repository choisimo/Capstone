import { useCallback, useEffect, useMemo, useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Calendar, Filter, Download, RefreshCw, BarChart3, TrendingUp, Users, MessageSquare } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell } from "recharts";
import {
  fetchSentimentStats,
  fetchSentimentTrend,
  fetchDashboardTopIssues,
  fetchDashboardOverview,
  type SentimentStats,
  type IssueSummary,
  type DashboardOverview,
} from "@/lib/api";

type TrendDatum = {
  date: string;
  positive: number;
  negative: number;
  neutral: number;
  total: number;
};

type ChannelDatum = {
  name: string;
  value: number;
};

const DATE_RANGE_MAP: Record<string, number> = {
  "1d": 1,
  "7d": 7,
  "30d": 30,
  "90d": 90,
};

const DATE_RANGE_LABEL: Record<string, string> = {
  "1d": "1일",
  "7d": "7일",
  "30d": "30일",
  "90d": "90일",
};

function buildDateRange(rangeKey: string) {
  const days = DATE_RANGE_MAP[rangeKey] ?? 7;
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - (days - 1));

  return {
    from: start.toISOString().split("T")[0],
    to: end.toISOString().split("T")[0],
  };
}

function transformTrend(points: Array<{ date: string; sentiment_score: number; volume: number }> = []): TrendDatum[] {
  return points.map((point) => {
    const total = point.volume ?? 0;
    const positiveRatio = Math.min(1, Math.max(0, (point.sentiment_score + 1) / 2));
    const positive = Math.round(total * positiveRatio);
    const negative = Math.max(0, total - positive);
    return {
      date: new Date(point.date).toLocaleDateString("ko-KR", { month: "2-digit", day: "2-digit" }),
      positive,
      negative,
      neutral: 0,
      total,
    };
  });
}

export default function Analytics() {
  const [dateRange, setDateRange] = useState("7d");
  const [activeTab, setActiveTab] = useState("overview");
  const [sentimentStats, setSentimentStats] = useState<SentimentStats | null>(null);
  const [trendData, setTrendData] = useState<TrendDatum[]>([]);
  const [topicData, setTopicData] = useState<IssueSummary[]>([]);
  const [channelData, setChannelData] = useState<ChannelDatum[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadAnalyticsData = useCallback(async () => {
    const { from, to } = buildDateRange(dateRange);
    setLoading(true);
    setError(null);

    try {
      const stats = await fetchSentimentStats({ from, to });
      setSentimentStats(stats);

      const [trendRes, issueRes, overviewRes] = await Promise.all([
        fetchSentimentTrend({ from, to, agg: "day" }).catch((err) => {
          console.error("Failed to load sentiment trend", err);
          return null;
        }),
        fetchDashboardTopIssues(5).catch((err) => {
          console.error("Failed to load top issues", err);
          return [] as IssueSummary[];
        }),
        fetchDashboardOverview().catch((err) => {
          console.error("Failed to load dashboard overview", err);
          return null as DashboardOverview | null;
        }),
      ]);

      setTrendData(transformTrend(trendRes?.trends || []));
      setTopicData(issueRes || []);

      const channels = (overviewRes?.channels || []).map((channel) => ({
        name: channel.name,
        value: (channel.count ?? (channel as any).mentions ?? 0) as number,
      }));
      setChannelData(channels);
    } catch (err) {
      console.error("Failed to load analytics data", err);
      setError("데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.");
    } finally {
      setLoading(false);
    }
  }, [dateRange]);

  useEffect(() => {
    loadAnalyticsData();
  }, [loadAnalyticsData]);

  const totalMentions = sentimentStats?.total ?? 0;
  const sentimentScore = useMemo(() => {
    if (!sentimentStats) return 0;
    const delta = sentimentStats.positive - sentimentStats.negative;
    const normalized = delta / Math.max(1, sentimentStats.total);
    // scale -1~1 to 0~10 for display
    return ((normalized + 1) / 2) * 10;
  }, [sentimentStats]);

  const sentimentPieData = useMemo(() => {
    if (!sentimentStats) return [];
    return [
      { name: "긍정", value: sentimentStats.positive, color: "hsl(var(--sentiment-positive))" },
      { name: "중립", value: sentimentStats.neutral, color: "hsl(var(--sentiment-neutral))" },
      { name: "부정", value: sentimentStats.negative, color: "hsl(var(--sentiment-negative))" },
    ];
  }, [sentimentStats]);

  const overviewCards = useMemo(
    () => [
      {
        title: "총 언급량",
        value: totalMentions ? totalMentions.toLocaleString() : "-",
        subtitle: `최근 ${DATE_RANGE_LABEL[dateRange] ?? dateRange} 기준`,
        icon: MessageSquare,
        accent: "text-primary",
      },
      {
        title: "평균 감정 점수",
        value: sentimentStats ? sentimentScore.toFixed(1) : "-",
        subtitle: "0~10 (높을수록 긍정)",
        icon: TrendingUp,
        accent: "text-sentiment-positive",
      },
      {
        title: "활성 토픽",
        value: topicData.length ? topicData.length.toString() : "0",
        subtitle: "최근 인기 이슈",
        icon: BarChart3,
        accent: "text-info",
      },
      {
        title: "모니터링 채널",
        value: channelData.length ? channelData.length.toString() : "-",
        subtitle: channelData.length ? `${channelData.length}개 채널` : "데이터 없음",
        icon: Users,
        accent: "text-warning",
      },
    ], [totalMentions, dateRange, sentimentStats, sentimentScore, topicData.length, channelData.length]
  );

  const handleRefresh = () => {
    loadAnalyticsData();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <PageHeader
        title="분석 대시보드"
        description="상세한 여론 분석과 심층 인사이트를 제공합니다. 필터를 조합하여 원하는 데이터를 분석하세요."
        badge="실시간"
        actions={
          <div className="flex gap-2">
            <Select value={dateRange} onValueChange={setDateRange}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1d">1일</SelectItem>
                <SelectItem value="7d">7일</SelectItem>
                <SelectItem value="30d">30일</SelectItem>
                <SelectItem value="90d">90일</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              필터
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              내보내기
            </Button>
            <Button size="sm" onClick={handleRefresh} disabled={loading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
              새로고침
            </Button>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {error && (
          <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
            {error}
          </div>
        )}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 bg-muted/50">
            <TabsTrigger value="overview" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              전체 개요
            </TabsTrigger>
            <TabsTrigger value="sentiment" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              감정 분석
            </TabsTrigger>
            <TabsTrigger value="topics" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              토픽 분석
            </TabsTrigger>
            <TabsTrigger value="channels" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              채널 분석
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {overviewCards.map((card) => {
                const Icon = card.icon;
                return (
                  <GlassCard key={card.title} className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">{card.title}</p>
                        <p className="text-2xl font-bold">{card.value}</p>
                        <p className="text-xs text-muted-foreground">{card.subtitle}</p>
                      </div>
                      <Icon className={`h-8 w-8 ${card.accent} opacity-80`} />
                    </div>
                  </GlassCard>
                );
              })}
            </div>

            <GlassCard>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  감정 추이 분석
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  {trendData.length === 0 ? (
                    <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                      데이터가 없습니다
                    </div>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={trendData}>
                        <defs>
                          <linearGradient id="positiveGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="hsl(var(--sentiment-positive))" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="hsl(var(--sentiment-positive))" stopOpacity={0.1}/>
                          </linearGradient>
                          <linearGradient id="negativeGradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="hsl(var(--sentiment-negative))" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="hsl(var(--sentiment-negative))" stopOpacity={0.1}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                        <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                        <Tooltip 
                          contentStyle={{
                            backgroundColor: "hsl(var(--background))",
                            border: "1px solid hsl(var(--border))",
                            borderRadius: "8px"
                          }}
                        />
                        <Area 
                          type="monotone" 
                          dataKey="positive" 
                          stackId="1"
                          stroke="hsl(var(--sentiment-positive))" 
                          fill="url(#positiveGradient)"
                          strokeWidth={2}
                        />
                        <Area 
                          type="monotone" 
                          dataKey="neutral" 
                          stackId="1"
                          stroke="hsl(var(--sentiment-neutral))" 
                          fill="hsl(var(--sentiment-neutral-light))"
                          strokeWidth={2}
                        />
                        <Area 
                          type="monotone" 
                          dataKey="negative" 
                          stackId="1"
                          stroke="hsl(var(--sentiment-negative))" 
                          fill="url(#negativeGradient)"
                          strokeWidth={2}
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </CardContent>
            </GlassCard>
          </TabsContent>

          <TabsContent value="sentiment" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <GlassCard>
                <CardHeader>
                  <CardTitle>감정 분포</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    {sentimentPieData.length === 0 ? (
                      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                        데이터가 없습니다
                      </div>
                    ) : (
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={sentimentPieData}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={100}
                            dataKey="value"
                            strokeWidth={2}
                            stroke="hsl(var(--background))"
                          >
                            {sentimentPieData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                </CardContent>
              </GlassCard>

              <GlassCard>
                <CardHeader>
                  <CardTitle>감정별 언급량 추이</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    {trendData.length === 0 ? (
                      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                        데이터가 없습니다
                      </div>
                    ) : (
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={trendData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                          <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                          <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                          <Tooltip />
                          <Line 
                            type="monotone" 
                            dataKey="positive" 
                            stroke="hsl(var(--sentiment-positive))" 
                            strokeWidth={3}
                            dot={{ fill: "hsl(var(--sentiment-positive))", strokeWidth: 2, r: 4 }}
                          />
                          <Line 
                            type="monotone" 
                            dataKey="negative" 
                            stroke="hsl(var(--sentiment-negative))" 
                            strokeWidth={3}
                            dot={{ fill: "hsl(var(--sentiment-negative))", strokeWidth: 2, r: 4 }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    )}
                  </div>
                </CardContent>
              </GlassCard>
            </div>
          </TabsContent>

          <TabsContent value="topics" className="space-y-6">
            <GlassCard>
              <CardHeader>
                <CardTitle>주요 토픽 분석</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {topicData.length === 0 ? (
                    <div className="flex h-24 items-center justify-center text-sm text-muted-foreground">
                      이슈 데이터를 불러오지 못했습니다.
                    </div>
                  ) : (
                    topicData.map((topic, index) => (
                      <div key={topic.id ?? index} className="flex items-center justify-between p-4 rounded-lg border border-border/50 bg-muted/20 hover:bg-muted/40 transition-colors">
                        <div className="flex items-center gap-4">
                          <div className="text-lg font-semibold text-muted-foreground">
                            #{index + 1}
                          </div>
                          <div>
                            <h3 className="font-medium">{topic.topic}</h3>
                            <p className="text-sm text-muted-foreground">{(topic.mentions ?? 0).toLocaleString()} 언급</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <Badge 
                            variant={topic.sentiment === "positive" ? "default" : topic.sentiment === "negative" ? "destructive" : "secondary"}
                            className="text-xs"
                          >
                            {topic.sentiment === "positive" ? "긍정" : topic.sentiment === "negative" ? "부정" : "중립"}
                          </Badge>
                          <div className={`text-sm font-medium ${topic.trend?.toString().startsWith("+") ? "text-sentiment-positive" : "text-sentiment-negative"}`}>
                            {topic.trend ?? "-"}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </GlassCard>
          </TabsContent>

          <TabsContent value="channels" className="space-y-6">
            <GlassCard>
              <CardHeader>
                <CardTitle>채널별 활동 분석</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  {channelData.length === 0 ? (
                    <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                      채널 데이터가 아직 제공되지 않았습니다.
                    </div>
                  ) : (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={channelData} layout="horizontal">
                        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                        <XAxis type="number" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                        <YAxis dataKey="name" type="category" stroke="hsl(var(--muted-foreground))" fontSize={12} width={100} />
                        <Tooltip />
                        <Bar dataKey="value" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </div>
              </CardContent>
            </GlassCard>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}