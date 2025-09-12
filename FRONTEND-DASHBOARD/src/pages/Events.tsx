import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Calendar, TrendingUp, BarChart3, Download, AlertTriangle, CheckCircle } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, ReferenceLine } from "recharts";

const policyEvents = [
  {
    id: 1,
    title: "보험료율 13% 인상 발표",
    date: "2024-01-05",
    type: "정책발표",
    status: "분석완료",
    description: "국민연금 보험료율을 현행 9%에서 13%로 단계적 인상한다고 발표",
    impact: -2.3,
    confidence: 85,
    beforeSentiment: 6.8,
    afterSentiment: 4.5,
    mentions: { before: 234, after: 1247 }
  },
  {
    id: 2,
    title: "청년 가입 지원책 확대",
    date: "2024-01-03",
    type: "지원정책",
    status: "분석완료",
    description: "청년층 국민연금 가입률 제고를 위한 지원 프로그램 확대 발표",
    impact: +1.8,
    confidence: 92,
    beforeSentiment: 5.2,
    afterSentiment: 7.0,
    mentions: { before: 89, after: 534 }
  },
  {
    id: 3,
    title: "기금운용 수익률 공개",
    date: "2024-01-01",
    type: "정보공개",
    status: "분석중",
    description: "2023년 국민연금 기금운용 수익률 8.7% 달성 발표",
    impact: +0.5,
    confidence: 78,
    beforeSentiment: 6.1,
    afterSentiment: 6.6,
    mentions: { before: 156, after: 298 }
  }
];

const impactAnalysisData = [
  { time: "-24h", sentiment: 6.8, mentions: 45 },
  { time: "-18h", sentiment: 6.7, mentions: 52 },
  { time: "-12h", sentiment: 6.5, mentions: 67 },
  { time: "-6h", sentiment: 6.4, mentions: 89 },
  { time: "발표", sentiment: 6.8, mentions: 234 },
  { time: "+6h", sentiment: 5.2, mentions: 567 },
  { time: "+12h", sentiment: 4.8, mentions: 892 },
  { time: "+18h", sentiment: 4.5, mentions: 1134 },
  { time: "+24h", sentiment: 4.3, mentions: 1247 },
];

export default function Events() {
  const [selectedEvent, setSelectedEvent] = useState(policyEvents[0]);
  const [analysisType, setAnalysisType] = useState("impact");
  const [compareMode, setCompareMode] = useState(false);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "분석완료":
        return <Badge className="bg-sentiment-positive/10 text-sentiment-positive border-sentiment-positive/20">분석완료</Badge>;
      case "분석중":
        return <Badge className="bg-warning/10 text-warning border-warning/20">분석중</Badge>;
      case "대기중":
        return <Badge variant="secondary">대기중</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getImpactColor = (impact: number) => {
    if (impact > 0) return "text-sentiment-positive";
    if (impact < 0) return "text-sentiment-negative";
    return "text-muted-foreground";
  };

  const getImpactIcon = (impact: number) => {
    if (impact > 0) return <TrendingUp className="h-4 w-4" />;
    if (impact < 0) return <AlertTriangle className="h-4 w-4" />;
    return <CheckCircle className="h-4 w-4" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <PageHeader
        title="이벤트 분석"
        description="정책 발표나 주요 이벤트가 여론에 미치는 영향을 ITS(Interrupted Time Series) 분석으로 측정합니다."
        badge="고급 분석"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setCompareMode(!compareMode)}>
              <BarChart3 className="h-4 w-4 mr-2" />
              {compareMode ? "비교 종료" : "이벤트 비교"}
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              보고서 다운로드
            </Button>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Event Timeline */}
          <div className="lg:col-span-1">
            <GlassCard>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Calendar className="h-4 w-4" />
                  정책 이벤트
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-96">
                  <div className="space-y-2 p-4">
                    {policyEvents.map((event) => (
                      <div
                        key={event.id}
                        className={`p-3 rounded-lg cursor-pointer transition-all ${
                          selectedEvent.id === event.id 
                            ? "bg-primary/10 border border-primary/20" 
                            : "bg-muted/10 hover:bg-muted/20"
                        }`}
                        onClick={() => setSelectedEvent(event)}
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-muted-foreground">{event.date}</span>
                            {getStatusBadge(event.status)}
                          </div>
                          <h4 className="font-medium text-sm leading-tight">{event.title}</h4>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-xs">
                              {event.type}
                            </Badge>
                            <div className={`flex items-center gap-1 text-xs font-medium ${getImpactColor(event.impact)}`}>
                              {getImpactIcon(event.impact)}
                              {event.impact > 0 ? '+' : ''}{event.impact.toFixed(1)}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </GlassCard>
          </div>

          {/* Analysis Details */}
          <div className="lg:col-span-3">
            <div className="space-y-6">
              {/* Event Summary */}
              <GlassCard>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>{selectedEvent.title}</CardTitle>
                    <div className="flex items-center gap-2">
                      {getStatusBadge(selectedEvent.status)}
                      <Badge variant="outline" className="text-xs">
                        신뢰도 {selectedEvent.confidence}%
                      </Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground mb-4">{selectedEvent.description}</p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 rounded-lg bg-muted/20">
                      <div className="text-center">
                        <p className="text-sm text-muted-foreground">영향 점수</p>
                        <p className={`text-2xl font-bold ${getImpactColor(selectedEvent.impact)}`}>
                          {selectedEvent.impact > 0 ? '+' : ''}{selectedEvent.impact.toFixed(1)}
                        </p>
                        <p className="text-xs text-muted-foreground">감정 변화량</p>
                      </div>
                    </div>

                    <div className="p-4 rounded-lg bg-muted/20">
                      <div className="text-center">
                        <p className="text-sm text-muted-foreground">감정 점수</p>
                        <div className="flex items-center justify-center gap-2">
                          <span className="text-lg font-bold">{selectedEvent.beforeSentiment}</span>
                          <span className="text-muted-foreground">→</span>
                          <span className={`text-lg font-bold ${getImpactColor(selectedEvent.afterSentiment - selectedEvent.beforeSentiment)}`}>
                            {selectedEvent.afterSentiment}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground">이전 → 이후</p>
                      </div>
                    </div>

                    <div className="p-4 rounded-lg bg-muted/20">
                      <div className="text-center">
                        <p className="text-sm text-muted-foreground">언급량 변화</p>
                        <div className="flex items-center justify-center gap-2">
                          <span className="text-lg font-bold">{selectedEvent.mentions.before}</span>
                          <span className="text-muted-foreground">→</span>
                          <span className="text-lg font-bold text-primary">{selectedEvent.mentions.after}</span>
                        </div>
                        <p className="text-xs text-sentiment-positive">
                          +{Math.round(((selectedEvent.mentions.after - selectedEvent.mentions.before) / selectedEvent.mentions.before) * 100)}% 증가
                        </p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </GlassCard>

              {/* Analysis Tabs */}
              <Tabs value={analysisType} onValueChange={setAnalysisType}>
                <TabsList className="grid w-full grid-cols-3 bg-muted/50">
                  <TabsTrigger value="impact">영향 분석</TabsTrigger>
                  <TabsTrigger value="timeline">시계열 분석</TabsTrigger>
                  <TabsTrigger value="breakdown">세부 분석</TabsTrigger>
                </TabsList>

                <TabsContent value="impact" className="space-y-6">
                  <GlassCard>
                    <CardHeader>
                      <CardTitle className="flex items-center gap-2">
                        <BarChart3 className="h-5 w-5" />
                        ITS 분석 결과
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-80">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={impactAnalysisData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                            <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                            <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                            <Tooltip 
                              contentStyle={{
                                backgroundColor: "hsl(var(--background))",
                                border: "1px solid hsl(var(--border))",
                                borderRadius: "8px"
                              }}
                            />
                            <ReferenceLine x="발표" stroke="hsl(var(--primary))" strokeDasharray="5 5" />
                            <Line 
                              type="monotone" 
                              dataKey="sentiment" 
                              stroke="hsl(var(--sentiment-negative))" 
                              strokeWidth={3}
                              dot={{ fill: "hsl(var(--sentiment-negative))", strokeWidth: 2, r: 4 }}
                              name="감정 점수"
                            />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </GlassCard>
                </TabsContent>

                <TabsContent value="timeline" className="space-y-6">
                  <GlassCard>
                    <CardHeader>
                      <CardTitle>언급량 변화 추이</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="h-80">
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={impactAnalysisData}>
                            <defs>
                              <linearGradient id="mentionsGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                                <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0.1}/>
                              </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                            <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                            <YAxis stroke="hsl(var(--muted-foreground))" fontSize={12} />
                            <Tooltip />
                            <ReferenceLine x="발표" stroke="hsl(var(--primary))" strokeDasharray="5 5" />
                            <Area 
                              type="monotone" 
                              dataKey="mentions" 
                              stroke="hsl(var(--primary))" 
                              fill="url(#mentionsGradient)"
                              strokeWidth={2}
                            />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                    </CardContent>
                  </GlassCard>
                </TabsContent>

                <TabsContent value="breakdown" className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <GlassCard>
                      <CardHeader>
                        <CardTitle className="text-base">통계적 유의성</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">P-value:</span>
                          <span className="font-mono text-sm">0.003</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">R²:</span>
                          <span className="font-mono text-sm">0.78</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">신뢰구간:</span>
                          <span className="font-mono text-sm">95%</span>
                        </div>
                        <div className="pt-2 border-t border-border">
                          <Badge className="w-full justify-center bg-sentiment-positive/10 text-sentiment-positive">
                            통계적으로 유의한 영향
                          </Badge>
                        </div>
                      </CardContent>
                    </GlassCard>

                    <GlassCard>
                      <CardHeader>
                        <CardTitle className="text-base">추정 효과</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">즉시 효과:</span>
                          <span className="font-semibold text-sentiment-negative">-1.8점</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">24시간 효과:</span>
                          <span className="font-semibold text-sentiment-negative">-2.3점</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-sm text-muted-foreground">추정 지속기간:</span>
                          <span className="font-mono text-sm">7-14일</span>
                        </div>
                        <div className="pt-2 border-t border-border">
                          <Badge variant="destructive" className="w-full justify-center">
                            강한 부정적 영향
                          </Badge>
                        </div>
                      </CardContent>
                    </GlassCard>
                  </div>
                </TabsContent>
              </Tabs>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}