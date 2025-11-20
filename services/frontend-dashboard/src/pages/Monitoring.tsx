import { useState, useEffect } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GlassCard } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Activity, AlertTriangle, TrendingUp, Users, MessageSquare, Eye, Pause, Play } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

const realTimeData = [
  { time: "14:00", mentions: 45, sentiment: 6.8 },
  { time: "14:05", mentions: 52, sentiment: 6.5 },
  { time: "14:10", mentions: 48, sentiment: 6.9 },
  { time: "14:15", mentions: 67, sentiment: 6.2 },
  { time: "14:20", mentions: 59, sentiment: 6.7 },
  { time: "14:25", mentions: 73, sentiment: 5.8 },
  { time: "14:30", mentions: 81, sentiment: 5.5 },
];

const liveEvents = [
  { time: "14:32", type: "spike", content: "보험료율 관련 언급량 급증", severity: "high" },
  { time: "14:28", type: "sentiment", content: "연금개혁 토픽의 부정 감정 증가", severity: "medium" },
  { time: "14:25", type: "trend", content: "청년층 가입률 긍정 반응 지속", severity: "low" },
  { time: "14:20", type: "alert", content: "특정 키워드 임계치 초과", severity: "high" },
  { time: "14:15", type: "info", content: "새로운 이슈 토픽 감지", severity: "low" },
];

const activeUsers = [
  { platform: "네이버 뉴스", users: 1234, change: "+15%" },
  { platform: "커뮤니티", users: 892, change: "+8%" },
  { platform: "소셜미디어", users: 567, change: "-3%" },
  { platform: "온라인 미디어", users: 423, change: "+22%" },
];

export default function Monitoring() {
  const [isLive, setIsLive] = useState(true);
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "high": return "text-sentiment-negative";
      case "medium": return "text-warning";
      case "low": return "text-sentiment-positive";
      default: return "text-muted-foreground";
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "high": return <Badge variant="destructive">긴급</Badge>;
      case "medium": return <Badge variant="secondary" className="bg-warning/10 text-warning">주의</Badge>;
      case "low": return <Badge variant="secondary" className="bg-sentiment-positive/10 text-sentiment-positive">정보</Badge>;
      default: return <Badge variant="outline">일반</Badge>;
    }
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case "spike": return <TrendingUp className="h-4 w-4" />;
      case "alert": return <AlertTriangle className="h-4 w-4" />;
      case "sentiment": return <Activity className="h-4 w-4" />;
      default: return <MessageSquare className="h-4 w-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <PageHeader
        title="실시간 모니터링"
        description="국민연금 관련 온라인 여론을 실시간으로 모니터링하고 중요한 변화를 즉시 감지합니다."
        badge={isLive ? "LIVE" : "일시정지"}
        actions={
          <div className="flex items-center gap-3">
            <div className="text-sm text-muted-foreground font-mono">
              {currentTime.toLocaleTimeString()}
            </div>
            <Button
              variant={isLive ? "destructive" : "default"}
              size="sm"
              onClick={() => setIsLive(!isLive)}
            >
              {isLive ? (
                <>
                  <Pause className="h-4 w-4 mr-2" />
                  일시정지
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  시작
                </>
              )}
            </Button>
          </div>
        }
      />

      <div className="p-6 space-y-6">
        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <GlassCard className="p-6 border-l-4 border-l-sentiment-positive">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">실시간 언급</p>
                <p className="text-2xl font-bold">73</p>
                <p className="text-xs text-sentiment-positive">지난 5분</p>
              </div>
              <div className="relative">
                <MessageSquare className="h-8 w-8 text-sentiment-positive opacity-80" />
                {isLive && (
                  <div className="absolute -top-1 -right-1 h-3 w-3 bg-sentiment-positive rounded-full animate-pulse-glow"></div>
                )}
              </div>
            </div>
          </GlassCard>

          <GlassCard className="p-6 border-l-4 border-l-primary">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">감정 점수</p>
                <p className="text-2xl font-bold">5.5</p>
                <p className="text-xs text-sentiment-negative">-0.3 (5분 전)</p>
              </div>
              <Activity className="h-8 w-8 text-primary opacity-80" />
            </div>
          </GlassCard>

          <GlassCard className="p-6 border-l-4 border-l-warning">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">활성 사용자</p>
                <p className="text-2xl font-bold">3,116</p>
                <p className="text-xs text-sentiment-positive">+12% (1시간 전)</p>
              </div>
              <Users className="h-8 w-8 text-warning opacity-80" />
            </div>
          </GlassCard>

          <GlassCard className="p-6 border-l-4 border-l-sentiment-negative">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">경보 현황</p>
                <p className="text-2xl font-bold">2</p>
                <p className="text-xs text-sentiment-negative">긴급 1건, 주의 1건</p>
              </div>
              <AlertTriangle className="h-8 w-8 text-sentiment-negative opacity-80" />
            </div>
          </GlassCard>
        </div>

        {/* Real-time Charts and Events */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <GlassCard>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5" />
                  실시간 언급 추이
                </CardTitle>
                <div className="flex items-center gap-2">
                  {isLive && (
                    <>
                      <div className="h-2 w-2 bg-sentiment-positive rounded-full animate-pulse-glow"></div>
                      <span className="text-xs text-sentiment-positive font-medium">LIVE</span>
                    </>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={realTimeData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <YAxis yAxisId="left" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <YAxis yAxisId="right" orientation="right" stroke="hsl(var(--muted-foreground))" fontSize={12} />
                      <Tooltip 
                        contentStyle={{
                          backgroundColor: "hsl(var(--background))",
                          border: "1px solid hsl(var(--border))",
                          borderRadius: "8px"
                        }}
                      />
                      <Line 
                        yAxisId="left"
                        type="monotone" 
                        dataKey="mentions" 
                        stroke="hsl(var(--primary))" 
                        strokeWidth={3}
                        dot={{ fill: "hsl(var(--primary))", strokeWidth: 2, r: 4 }}
                        name="언급량"
                      />
                      <Line 
                        yAxisId="right"
                        type="monotone" 
                        dataKey="sentiment" 
                        stroke="hsl(var(--sentiment-positive))" 
                        strokeWidth={3}
                        dot={{ fill: "hsl(var(--sentiment-positive))", strokeWidth: 2, r: 4 }}
                        name="감정 점수"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </GlassCard>

            <GlassCard>
              <CardHeader>
                <CardTitle>플랫폼별 활성 사용자</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {activeUsers.map((platform, index) => (
                    <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-muted/20">
                      <div className="flex items-center gap-3">
                        <div className="h-3 w-3 bg-primary rounded-full"></div>
                        <span className="font-medium">{platform.platform}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-lg">{platform.users.toLocaleString()}</span>
                        <span className={`text-sm font-medium ${
                          platform.change.startsWith("+") ? "text-sentiment-positive" : "text-sentiment-negative"
                        }`}>
                          {platform.change}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </GlassCard>
          </div>

          <div>
            <GlassCard className="h-full">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Eye className="h-5 w-5" />
                  실시간 이벤트
                </CardTitle>
                {isLive && (
                  <Badge variant="outline" className="bg-sentiment-positive/10 text-sentiment-positive border-sentiment-positive/20">
                    실시간
                  </Badge>
                )}
              </CardHeader>
              <CardContent className="p-0">
                <ScrollArea className="h-96 px-6">
                  <div className="space-y-3 pb-4">
                    {liveEvents.map((event, index) => (
                      <div key={index} className="flex items-start gap-3 p-3 rounded-lg bg-muted/10 hover:bg-muted/20 transition-colors animate-fade-in">
                        <div className={`flex-shrink-0 ${getSeverityColor(event.severity)}`}>
                          {getEventIcon(event.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs text-muted-foreground font-mono">{event.time}</span>
                            {getSeverityBadge(event.severity)}
                          </div>
                          <p className="text-sm font-medium leading-relaxed">{event.content}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </GlassCard>
          </div>
        </div>
      </div>
    </div>
  );
}