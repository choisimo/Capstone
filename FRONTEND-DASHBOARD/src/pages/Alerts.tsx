import { useEffect, useMemo, useState } from "react";
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
import {
  fetchAlerts,
  acknowledgeAlert as apiAcknowledgeAlert,
  resolveAlert as apiResolveAlert,
  fetchAlertRules,
  toggleAlertRule as apiToggleAlertRule,
} from "@/lib/api";

type Severity = "low" | "medium" | "high" | "critical";
type Status = "pending" | "active" | "resolved" | "dismissed";

type AlertItem = {
  id: number;
  title: string;
  message: string;
  severity: Severity;
  status: Status;
  triggered_at: string;
  acknowledged_at?: string | null;
  acknowledged_by?: string | null;
  source_service?: string | null;
  threshold_value?: number | null;
  actual_value?: number | null;
  rule_id: number;
};

type AlertRule = {
  id: number;
  name: string;
  description?: string;
  severity: Severity;
  is_active: boolean;
  notification_channels?: string[];
  conditions?: Record<string, unknown>;
};

export default function Alerts() {
  const [activeTab, setActiveTab] = useState("alerts");
  const [filterSeverity, setFilterSeverity] = useState<string>("all");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [items, setItems] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rules, setRules] = useState<AlertRule[]>([]);
  const [rulesLoading, setRulesLoading] = useState(false);

  // 서버 상태를 UI 상태로 매핑
  const toUiStatus = (a: AlertItem): "unread" | "acknowledged" | "resolved" => {
    if (a.status === "resolved" || a.status === "dismissed") return "resolved";
    if (a.acknowledged_at) return "acknowledged";
    return "unread"; // pending/active & not acknowledged
  };

  const loadData = async () => {
    setLoading(true);
    setRulesLoading(true);
    setError(null);
    try {
      const [alertsData, rulesData] = await Promise.all([
        fetchAlerts({ limit: 200 }),
        fetchAlertRules({ limit: 200 }),
      ]);
      setItems(alertsData || []);
      setRules(rulesData || []);
    } catch (e: any) {
      setError(e?.message || "알림 데이터를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
      setRulesLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case "high":
        return <Badge variant="destructive">긴급</Badge>;
      case "critical":
        return <Badge className="bg-red-600 text-white">치명</Badge>;
      case "medium":
        return <Badge className="bg-warning/10 text-warning border-warning/20">주의</Badge>;
      case "low":
        return <Badge className="bg-sentiment-positive/10 text-sentiment-positive border-sentiment-positive/20">정보</Badge>;
      default:
        return <Badge variant="outline">일반</Badge>;
    }
  };

  const getStatusIcon = (status: "unread" | "acknowledged" | "resolved") => {
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

  const getTypeIcon = () => <Bell className="h-4 w-4" />; // 목록에서는 유형 정보가 없으므로 기본 아이콘 사용

  const getUserIdFromToken = (): string => {
    try {
      const token =
        localStorage.getItem('auth_token') ||
        localStorage.getItem('access_token') ||
        sessionStorage.getItem('auth_token') ||
        sessionStorage.getItem('access_token');
      if (!token) return "dashboard-user";
      const parts = token.split('.');
      if (parts.length !== 3) return "dashboard-user";
      const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
      return payload?.sub || payload?.user_id || payload?.username || "dashboard-user";
    } catch {
      return "dashboard-user";
    }
  };

  const onAcknowledge = async (alertId: number) => {
    try {
      const userId = getUserIdFromToken();
      await apiAcknowledgeAlert(alertId, userId);
      // 낙관적 업데이트 또는 재조회
      setItems((prev) => prev.map(a => a.id === alertId ? { ...a, acknowledged_at: new Date().toISOString() } : a));
    } catch (e: any) {
      setError(e?.message || "알림 확인 처리에 실패했습니다.");
    }
  };

  const onResolve = async (alertId: number) => {
    try {
      const userId = getUserIdFromToken();
      await apiResolveAlert(alertId, userId);
      setItems((prev) => prev.map(a => a.id === alertId ? { ...a, status: "resolved" } as AlertItem : a));
    } catch (e: any) {
      setError(e?.message || "알림 해결 처리에 실패했습니다.");
    }
  };

  const onToggleRule = async (ruleId: number) => {
    try {
      const res = await apiToggleAlertRule(ruleId);
      const updated = res?.rule;
      setRules((prev) => prev.map(r => r.id === ruleId ? { ...r, is_active: updated?.is_active ?? !r.is_active } : r));
    } catch (e: any) {
      setError(e?.message || "규칙 토글에 실패했습니다.");
    }
  };

  const filteredAlerts = useMemo(() => {
    return items.filter((alert) => {
      if (filterSeverity !== "all" && alert.severity !== filterSeverity) return false;
      const ui = toUiStatus(alert);
      if (filterStatus !== "all" && ui !== filterStatus) return false;
      return true;
    });
  }, [items, filterSeverity, filterStatus]);

  const unreadCount = useMemo(() => items.filter(a => toUiStatus(a) === "unread").length, [items]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <PageHeader
        title="알림 센터"
        description="중요한 여론 변화와 이상 상황을 실시간으로 감지하여 알려드립니다."
        badge={unreadCount > 0 ? `${unreadCount}개 미확인` : "최신"}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setActiveTab("settings") }>
              <Settings className="h-4 w-4 mr-2" />
              알림 설정
            </Button>
            <Button size="sm" onClick={async () => {
              const userId = getUserIdFromToken();
              const targets = items.filter(a => toUiStatus(a) === "unread");
              for (const a of targets) {
                try { await apiAcknowledgeAlert(a.id, userId); } catch {}
              }
              await loadData();
            }}>
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
              {loading && (
                <GlassCard>
                  <CardContent className="p-6 text-sm text-muted-foreground">로딩 중...</CardContent>
                </GlassCard>
              )}
              {error && (
                <GlassCard>
                  <CardContent className="p-6 text-sm text-destructive">{error}</CardContent>
                </GlassCard>
              )}
              {!loading && !error && filteredAlerts.map((alert) => (
                <GlassCard key={alert.id} className={`hover:shadow-elevated transition-all ${
                  toUiStatus(alert) === "unread" ? "border-l-4 border-l-primary" : ""
                }`}>
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4 flex-1">
                        <div className="flex items-center gap-2 mt-1">
                          {getStatusIcon(toUiStatus(alert))}
                          {getTypeIcon()}
                        </div>
                        
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-3">
                            <h3 className="font-semibold">{alert.title}</h3>
                            {getSeverityBadge(alert.severity)}
                          </div>
                          
                          <p className="text-sm text-muted-foreground leading-relaxed">
                            {alert.message}
                          </p>
                          
                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {new Date(alert.triggered_at).toLocaleString()}
                            </div>
                            {alert.source_service && <div>출처: {alert.source_service}</div>}
                            <div>규칙 ID: {alert.rule_id}</div>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-xs">
                              {alert.actual_value !== undefined && alert.actual_value !== null ? `값: ${alert.actual_value}` : "알림"}
                            </Badge>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-2 ml-4">
                        {toUiStatus(alert) === "unread" && (
                          <Button variant="outline" size="sm" onClick={() => onAcknowledge(alert.id)}>
                            <Eye className="h-4 w-4 mr-2" />
                            확인
                          </Button>
                        )}
                        <Button variant="ghost" size="sm" onClick={() => onResolve(alert.id)}>
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </GlassCard>
              ))}

              {!loading && !error && filteredAlerts.length === 0 && (
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
                {rulesLoading && (
                  <div className="p-4 text-sm text-muted-foreground">규칙 로딩 중...</div>
                )}
                {!rulesLoading && rules.map((rule) => (
                  <div key={rule.id} className="flex items-start justify-between p-4 rounded-lg border border-border/50 bg-muted/10">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="font-medium">{rule.name}</h4>
                        <Badge variant="outline" className="text-xs">
                          중요도: {rule.severity}
                        </Badge>
                        <Switch checked={rule.is_active} onCheckedChange={() => onToggleRule(rule.id)} />
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">
                        {rule.description}
                      </p>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">알림 채널:</span>
                        {(rule.notification_channels || []).map((channel) => (
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