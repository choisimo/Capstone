import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Calendar, Filter, Download, RefreshCw, BarChart3, TrendingUp, Users, MessageSquare } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell } from "recharts";

const sentimentTrendData = [
  { date: "2024-01-01", positive: 45, neutral: 35, negative: 20, total: 1200 },
  { date: "2024-01-02", positive: 42, neutral: 38, negative: 20, total: 1450 },
  { date: "2024-01-03", positive: 40, neutral: 35, negative: 25, total: 1380 },
  { date: "2024-01-04", positive: 38, neutral: 37, negative: 25, total: 1620 },
  { date: "2024-01-05", positive: 42, neutral: 35, negative: 23, total: 1550 },
  { date: "2024-01-06", positive: 44, neutral: 34, negative: 22, total: 1720 },
  { date: "2024-01-07", positive: 46, neutral: 32, negative: 22, total: 1890 },
];

const channelData = [
  { name: "네이버 뉴스", value: 4234, color: "hsl(var(--primary))" },
  { name: "커뮤니티", value: 3127, color: "hsl(var(--sentiment-positive))" },
  { name: "소셜미디어", value: 2891, color: "hsl(var(--sentiment-neutral))" },
  { name: "온라인 미디어", value: 2295, color: "hsl(var(--sentiment-negative))" },
];

const topicData = [
  { topic: "보험료율", mentions: 1247, sentiment: "negative", trend: "+15%" },
  { topic: "수급연령", mentions: 892, sentiment: "negative", trend: "+8%" },
  { topic: "가입률", mentions: 534, sentiment: "positive", trend: "+22%" },
  { topic: "연금개혁", mentions: 423, sentiment: "neutral", trend: "+3%" },
  { topic: "기금운용", mentions: 298, sentiment: "positive", trend: "-5%" },
];

export default function Analytics() {
  const [dateRange, setDateRange] = useState("7d");
  const [activeTab, setActiveTab] = useState("overview");

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
            <Button size="sm">
              <RefreshCw className="h-4 w-4 mr-2" />
              새로고침
            </Button>
          </div>
        }
      />

      <div className="p-6 space-y-6">
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
              <GlassCard className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">총 언급량</p>
                    <p className="text-2xl font-bold">12,547</p>
                    <p className="text-xs text-sentiment-positive">+8.2% 전일 대비</p>
                  </div>
                  <MessageSquare className="h-8 w-8 text-primary opacity-80" />
                </div>
              </GlassCard>

              <GlassCard className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">평균 감정 점수</p>
                    <p className="text-2xl font-bold">7.2</p>
                    <p className="text-xs text-sentiment-negative">-0.3 전일 대비</p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-sentiment-positive opacity-80" />
                </div>
              </GlassCard>

              <GlassCard className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">활성 토픽</p>
                    <p className="text-2xl font-bold">18</p>
                    <p className="text-xs text-sentiment-positive">+3 신규</p>
                  </div>
                  <BarChart3 className="h-8 w-8 text-info opacity-80" />
                </div>
              </GlassCard>

              <GlassCard className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">참여 사용자</p>
                    <p className="text-2xl font-bold">8,934</p>
                    <p className="text-xs text-sentiment-positive">+12.1% 전일 대비</p>
                  </div>
                  <Users className="h-8 w-8 text-warning opacity-80" />
                </div>
              </GlassCard>
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
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={sentimentTrendData}>
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
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={[
                            { name: "긍정", value: 42, color: "hsl(var(--sentiment-positive))" },
                            { name: "중립", value: 35, color: "hsl(var(--sentiment-neutral))" },
                            { name: "부정", value: 23, color: "hsl(var(--sentiment-negative))" },
                          ]}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={100}
                          dataKey="value"
                          strokeWidth={2}
                          stroke="hsl(var(--background))"
                        >
                          {[
                            { name: "긍정", value: 42, color: "hsl(var(--sentiment-positive))" },
                            { name: "중립", value: 35, color: "hsl(var(--sentiment-neutral))" },
                            { name: "부정", value: 23, color: "hsl(var(--sentiment-negative))" },
                          ].map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </GlassCard>

              <GlassCard>
                <CardHeader>
                  <CardTitle>감정별 언급량 추이</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={sentimentTrendData}>
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
                  {topicData.map((topic, index) => (
                    <div key={index} className="flex items-center justify-between p-4 rounded-lg border border-border/50 bg-muted/20 hover:bg-muted/40 transition-colors">
                      <div className="flex items-center gap-4">
                        <div className="text-lg font-semibold text-muted-foreground">
                          #{index + 1}
                        </div>
                        <div>
                          <h3 className="font-medium">{topic.topic}</h3>
                          <p className="text-sm text-muted-foreground">{topic.mentions.toLocaleString()} 언급</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge 
                          variant={topic.sentiment === "positive" ? "default" : topic.sentiment === "negative" ? "destructive" : "secondary"}
                          className="text-xs"
                        >
                          {topic.sentiment === "positive" ? "긍정" : topic.sentiment === "negative" ? "부정" : "중립"}
                        </Badge>
                        <div className={`text-sm font-medium ${topic.trend.startsWith("+") ? "text-sentiment-positive" : "text-sentiment-negative"}`}>
                          {topic.trend}
                        </div>
                      </div>
                    </div>
                  ))}
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
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={channelData} layout="horizontal">
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis type="number" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <YAxis dataKey="name" type="category" stroke="hsl(var(--muted-foreground))" fontSize={12} width={100} />
                      <Tooltip />
                      <Bar dataKey="value" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </GlassCard>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}