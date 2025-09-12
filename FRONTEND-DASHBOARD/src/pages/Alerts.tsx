import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AlertTriangle, Bell, Settings, Eye, EyeOff, Check, X, Clock, Mail, MessageSquare, TrendingDown } from "lucide-react";

const alerts = [
  {
    id: 1,
    title: "보험료율 언급량 급증 감지",
    description: "최근 1시간 동안 '보험료율' 관련 언급이 평소 대비 300% 증가했습니다.",
    severity: "high",
    timestamp: "2024-01-07 14:32",
    status: "unread",
    type: "volume_spike",
    value: "1,247 언급 (+300%)",
    source: "자동 감지",
    rule: "언급량 증가율 > 200%"
  },
  {
    id: 2,
    title: "감정 점수 임계치 하락",
    description: "연금개혁 토픽의 감정 점수가 임계값(5.0) 이하로 하락했습니다.",
    severity: "medium",
    timestamp: "2024-01-07 13:45",
    status: "acknowledged",
    type: "sentiment_drop",
    value: "4.2점 (임계값: 5.0)",
    source: "감정 모니터링",
    rule: "감정 점수 < 5.0"
  },
  {
    id: 3,
    title: "새로운 이슈 키워드 감지",
    description: "'연금 사각지대'라는 새로운 키워드가 빈번하게 언급되고 있습니다.",
    severity: "low",
    timestamp: "2024-01-07 12:20",
    status: "resolved",
    type: "new_keyword",
    value: "89회 언급",
    source: "키워드 분석",
    rule: "신규 키워드 임계치 > 50"
  },
  {
    id: 4,
    title: "특정 커뮤니티 활동 급증",
    description: "클리앙 커뮤니티에서 국민연금 관련 활동이 급격히 증가했습니다.",
    severity: "medium",
    timestamp: "2024-01-07 11:15",
    status: "unread",
    type: "platform_spike",
    value: "234 포스트 (+180%)",
    source: "플랫폼 모니터링",
    rule: "플랫폼별 활동 > 150%"
  }
];

const alertRules = [
  {
    id: 1,
    name: "언급량 급증 감지",
    description: "특정 키워드의 언급량이 평소 대비 급격히 증가할 때",
    threshold: "200%",
    enabled: true,
    channels: ["email", "slack"]
  },
  {
    id: 2,
    name: "감정 점수 하락",
    description: "주요 토픽의 감정 점수가 임계값 이하로 떨어질 때",
    threshold: "5.0점",
    enabled: true,
    channels: ["email"]
  },
  {
    id: 3,
    name: "신규 키워드 등장",
    description: "새로운 이슈나 키워드가 빈번하게 언급될 때",
    threshold: "50회",
    enabled: true,
    channels: ["slack"]
  },
  {
    id: 4,
    name: "플랫폼별 활동 급증",
    description: "특정 플랫폼에서 비정상적인 활동 증가 감지",
    threshold: "150%",
    enabled: false,
    channels: ["email", "slack"]
  }
];

export default function Alerts() {
  const [activeTab, setActiveTab] = useState("alerts");
  const [filterSeverity, setFilterSeverity] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "high":
        return <Badge variant="destructive">긴급</Badge>;
      case "medium":
        return <Badge className="bg-warning/10 text-warning border-warning/20">주의</Badge>;
      case "low":
        return <Badge className="bg-sentiment-positive/10 text-sentiment-positive border-sentiment-positive/20">정보</Badge>;
      default:
        return <Badge variant="outline">일반</Badge>;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "unread":
        return <div className="h-2 w-2 bg-primary rounded-full"></div>;
      case "acknowledged":
        return <Eye className="h-4 w-4 text-warning" />;
      case "resolved":
        return <Check className="h-4 w-4 text-sentiment-positive" />;
      default:
        return null;
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "volume_spike":
        return <AlertTriangle className="h-4 w-4" />;
      case "sentiment_drop":
        return <TrendingDown className="h-4 w-4" />;
      case "new_keyword":
        return <MessageSquare className="h-4 w-4" />;
      case "platform_spike":
        return <Bell className="h-4 w-4" />;
      default:
        return <Bell className="h-4 w-4" />;
    }
  };

  const filteredAlerts = alerts.filter(alert => {
    if (filterSeverity !== "all" && alert.severity !== filterSeverity) return false;
    if (filterStatus !== "all" && alert.status !== filterStatus) return false;
    return true;
  });

  const unreadCount = alerts.filter(alert => alert.status === "unread").length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <PageHeader
        title="알림 센터"
        description="중요한 여론 변화와 이상 상황을 실시간으로 감지하여 알려드립니다."
        badge={unreadCount > 0 ? `${unreadCount}개 미확인` : "최신"}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Settings className="h-4 w-4 mr-2" />
              알림 설정
            </Button>
            <Button size="sm">
              모두 읽음 표시
            </Button>
          </div>
        }
      />

      <div className="p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 bg-muted/50">
            <TabsTrigger value="alerts" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              현재 알림 ({filteredAlerts.length})
            </TabsTrigger>
            <TabsTrigger value="history" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              알림 기록
            </TabsTrigger>
            <TabsTrigger value="settings" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              알림 규칙
            </TabsTrigger>
          </TabsList>

          <TabsContent value="alerts" className="space-y-6">
            {/* Filters */}
            <GlassCard>
              <CardContent className="p-4">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium">필터:</span>
                    <Select value={filterSeverity} onValueChange={setFilterSeverity}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">모든 등급</SelectItem>
                        <SelectItem value="high">긴급</SelectItem>
                        <SelectItem value="medium">주의</SelectItem>
                        <SelectItem value="low">정보</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select value={filterStatus} onValueChange={setFilterStatus}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">모든 상태</SelectItem>
                        <SelectItem value="unread">미확인</SelectItem>
                        <SelectItem value="acknowledged">확인됨</SelectItem>
                        <SelectItem value="resolved">해결됨</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="ml-auto text-sm text-muted-foreground">
                    {filteredAlerts.length}개 알림 표시
                  </div>
                </div>
              </CardContent>
            </GlassCard>

            {/* Alert List */}
            <div className="space-y-4">
              {filteredAlerts.map((alert) => (
                <GlassCard key={alert.id} className={`hover:shadow-elevated transition-all ${
                  alert.status === "unread" ? "border-l-4 border-l-primary" : ""
                }`}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4 flex-1">
                        <div className="flex items-center gap-2 mt-1">
                          {getStatusIcon(alert.status)}
                          {getTypeIcon(alert.type)}
                        </div>
                        
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-3">
                            <h3 className="font-semibold">{alert.title}</h3>
                            {getSeverityBadge(alert.severity)}
                          </div>
                          
                          <p className="text-sm text-muted-foreground leading-relaxed">
                            {alert.description}
                          </p>
                          
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {alert.timestamp}
                            </div>
                            <div>출처: {alert.source}</div>
                            <div>규칙: {alert.rule}</div>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-xs">
                              {alert.value}
                            </Badge>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2 ml-4">
                        {alert.status === "unread" && (
                          <Button variant="outline" size="sm">
                            <Eye className="h-4 w-4 mr-2" />
                            확인
                          </Button>
                        )}
                        <Button variant="ghost" size="sm">
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </GlassCard>
              ))}

              {filteredAlerts.length === 0 && (
                <GlassCard>
                  <CardContent className="p-8 text-center">
                    <Bell className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="font-semibold mb-2">알림이 없습니다</h3>
                    <p className="text-sm text-muted-foreground">
                      현재 설정된 필터에 해당하는 알림이 없습니다.
                    </p>
                  </CardContent>
                </GlassCard>
              )}
            </div>
          </TabsContent>

          <TabsContent value="history" className="space-y-6">
            <GlassCard>
              <CardHeader>
                <CardTitle>알림 기록</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center py-8">
                  <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <h3 className="font-semibold mb-2">알림 기록</h3>
                  <p className="text-sm text-muted-foreground">
                    지난 30일간의 알림 기록을 여기에서 확인할 수 있습니다.
                  </p>
                </div>
              </CardContent>
            </GlassCard>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            <GlassCard>
              <CardHeader>
                <CardTitle>알림 규칙 관리</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {alertRules.map((rule) => (
                  <div key={rule.id} className="flex items-start justify-between p-4 rounded-lg border border-border/50 bg-muted/10">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="font-medium">{rule.name}</h4>
                        <Badge variant="outline" className="text-xs">
                          임계값: {rule.threshold}
                        </Badge>
                        <Switch checked={rule.enabled} />
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">
                        {rule.description}
                      </p>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">알림 채널:</span>
                        {rule.channels.map((channel) => (
                          <Badge key={channel} variant="secondary" className="text-xs">
                            {channel === "email" ? <Mail className="h-3 w-3 mr-1" /> : <MessageSquare className="h-3 w-3 mr-1" />}
                            {channel}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <Button variant="ghost" size="sm">
                      <Settings className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
                
                <div className="pt-4 border-t border-border">
                  <Button variant="outline" className="w-full">
                    새 알림 규칙 추가
                  </Button>
                </div>
              </CardContent>
            </GlassCard>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}