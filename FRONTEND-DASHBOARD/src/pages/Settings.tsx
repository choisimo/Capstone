import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Settings as SettingsIcon, User, Bell, Database, Shield, Palette, Globe, Key } from "lucide-react";

const themes = [
  { name: "라이트", value: "light", description: "밝은 테마" },
  { name: "다크", value: "dark", description: "어두운 테마" },
  { name: "시스템", value: "system", description: "시스템 설정 따름" }
];

const languages = [
  { name: "한국어", value: "ko" },
  { name: "English", value: "en" }
];

const dataSources = [
  { name: "네이버 뉴스", enabled: true, status: "연결됨", lastSync: "2024-01-07 14:30" },
  { name: "다음 뉴스", enabled: true, status: "연결됨", lastSync: "2024-01-07 14:29" },
  { name: "클리앙", enabled: true, status: "연결됨", lastSync: "2024-01-07 14:32" },
  { name: "디시인사이드", enabled: false, status: "연결 안됨", lastSync: "2024-01-06 16:20" },
  { name: "트위터/X", enabled: true, status: "제한적", lastSync: "2024-01-07 14:25" },
  { name: "유튜브", enabled: false, status: "설정 필요", lastSync: "-" }
];

export default function Settings() {
  const [notifications, setNotifications] = useState({
    email: true,
    slack: true,
    realtime: true,
    summary: true
  });

  const [preferences, setPreferences] = useState({
    theme: "system",
    language: "ko",
    defaultPeriod: "7d",
    timezone: "Asia/Seoul"
  });

  const [apiKeys, setApiKeys] = useState([
    { name: "Slack Webhook", value: "xoxb-****-****-****", status: "활성", lastUsed: "2024-01-07 14:30" },
    { name: "Email Service", value: "smtp-****-****", status: "활성", lastUsed: "2024-01-07 13:45" },
    { name: "External API", value: "api-****-****", status: "비활성", lastUsed: "2024-01-05 10:20" }
  ]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <PageHeader
        title="설정"
        description="시스템 환경설정, 알림 설정, 데이터 소스 관리 등 개인 및 시스템 설정을 관리합니다."
        badge="시스템"
        actions={
          <Button>
            변경사항 저장
          </Button>
        }
      />

      <div className="p-6">
        <Tabs defaultValue="personal" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5 bg-muted/50">
            <TabsTrigger value="personal" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              개인 설정
            </TabsTrigger>
            <TabsTrigger value="notifications" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              알림 설정
            </TabsTrigger>
            <TabsTrigger value="data" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              데이터 소스
            </TabsTrigger>
            <TabsTrigger value="security" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              보안
            </TabsTrigger>
            <TabsTrigger value="system" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              시스템
            </TabsTrigger>
          </TabsList>

          <TabsContent value="personal" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <GlassCard>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5" />
                    프로필 설정
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">이름</Label>
                    <Input id="name" value="정책분석가" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">이메일</Label>
                    <Input id="email" value="analyst@nps.gov.kr" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="department">부서</Label>
                    <Input id="department" value="정책기획부" />
                  </div>
                </CardContent>
              </GlassCard>

              <GlassCard>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Palette className="h-5 w-5" />
                    화면 설정
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label>테마</Label>
                    <Select value={preferences.theme} onValueChange={(value) => setPreferences({...preferences, theme: value})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {themes.map((theme) => (
                          <SelectItem key={theme.value} value={theme.value}>
                            {theme.name} - {theme.description}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>언어</Label>
                    <Select value={preferences.language} onValueChange={(value) => setPreferences({...preferences, language: value})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {languages.map((lang) => (
                          <SelectItem key={lang.value} value={lang.value}>
                            {lang.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>기본 기간</Label>
                    <Select value={preferences.defaultPeriod} onValueChange={(value) => setPreferences({...preferences, defaultPeriod: value})}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1d">1일</SelectItem>
                        <SelectItem value="7d">7일</SelectItem>
                        <SelectItem value="30d">30일</SelectItem>
                        <SelectItem value="90d">90일</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </CardContent>
              </GlassCard>
            </div>
          </TabsContent>

          <TabsContent value="notifications" className="space-y-6">
            <GlassCard>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Bell className="h-5 w-5" />
                  알림 설정
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">이메일 알림</h4>
                    <p className="text-sm text-muted-foreground">중요한 알림을 이메일로 받습니다</p>
                  </div>
                  <Switch 
                    checked={notifications.email} 
                    onCheckedChange={(checked) => setNotifications({...notifications, email: checked})}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">Slack 알림</h4>
                    <p className="text-sm text-muted-foreground">Slack 채널로 실시간 알림을 받습니다</p>
                  </div>
                  <Switch 
                    checked={notifications.slack} 
                    onCheckedChange={(checked) => setNotifications({...notifications, slack: checked})}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">실시간 알림</h4>
                    <p className="text-sm text-muted-foreground">브라우저에서 실시간 알림을 받습니다</p>
                  </div>
                  <Switch 
                    checked={notifications.realtime} 
                    onCheckedChange={(checked) => setNotifications({...notifications, realtime: checked})}
                  />
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">일일 요약</h4>
                    <p className="text-sm text-muted-foreground">매일 오전 9시에 요약 리포트를 받습니다</p>
                  </div>
                  <Switch 
                    checked={notifications.summary} 
                    onCheckedChange={(checked) => setNotifications({...notifications, summary: checked})}
                  />
                </div>

                <div className="pt-4 border-t border-border">
                  <div className="space-y-2">
                    <Label htmlFor="slack-webhook">Slack Webhook URL</Label>
                    <Input 
                      id="slack-webhook" 
                      placeholder="https://hooks.slack.com/services/..." 
                      type="password"
                    />
                  </div>
                </div>
              </CardContent>
            </GlassCard>
          </TabsContent>

          <TabsContent value="data" className="space-y-6">
            <GlassCard>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  데이터 소스 관리
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {dataSources.map((source, index) => (
                    <div key={index} className="flex items-center justify-between p-4 rounded-lg border border-border/50 bg-muted/10">
                      <div className="flex items-center gap-4">
                        <Switch checked={source.enabled} />
                        <div>
                          <h4 className="font-medium">{source.name}</h4>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Badge 
                              variant={source.status === "연결됨" ? "default" : source.status === "제한적" ? "secondary" : "outline"}
                              className="text-xs"
                            >
                              {source.status}
                            </Badge>
                            <span>마지막 동기화: {source.lastSync}</span>
                          </div>
                        </div>
                      </div>
                      <Button variant="outline" size="sm">
                        설정
                      </Button>
                    </div>
                  ))}
                </div>
                
                <div className="mt-6 pt-4 border-t border-border">
                  <Button variant="outline" className="w-full">
                    새 데이터 소스 추가
                  </Button>
                </div>
              </CardContent>
            </GlassCard>
          </TabsContent>

          <TabsContent value="security" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <GlassCard>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5" />
                    보안 설정
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="current-password">현재 비밀번호</Label>
                    <Input id="current-password" type="password" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="new-password">새 비밀번호</Label>
                    <Input id="new-password" type="password" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="confirm-password">비밀번호 확인</Label>
                    <Input id="confirm-password" type="password" />
                  </div>
                  <Button className="w-full">
                    비밀번호 변경
                  </Button>
                </CardContent>
              </GlassCard>

              <GlassCard>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Key className="h-5 w-5" />
                    API 키 관리
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {apiKeys.map((key, index) => (
                      <div key={index} className="flex items-center justify-between p-3 rounded-lg bg-muted/20">
                        <div>
                          <h4 className="font-medium text-sm">{key.name}</h4>
                          <p className="text-xs text-muted-foreground font-mono">{key.value}</p>
                          <p className="text-xs text-muted-foreground">마지막 사용: {key.lastUsed}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge 
                            variant={key.status === "활성" ? "default" : "secondary"}
                            className="text-xs"
                          >
                            {key.status}
                          </Badge>
                          <Button variant="ghost" size="sm">
                            편집
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4">
                    <Button variant="outline" className="w-full">
                      새 API 키 생성
                    </Button>
                  </div>
                </CardContent>
              </GlassCard>
            </div>
          </TabsContent>

          <TabsContent value="system" className="space-y-6">
            <GlassCard>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <SettingsIcon className="h-5 w-5" />
                  시스템 설정
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <h4 className="font-medium">시스템 정보</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">버전:</span>
                        <span className="font-mono">v2.1.3</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">마지막 업데이트:</span>
                        <span className="font-mono">2024-01-05</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">데이터베이스:</span>
                        <Badge className="bg-sentiment-positive/10 text-sentiment-positive text-xs">정상</Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">캐시 상태:</span>
                        <Badge className="bg-sentiment-positive/10 text-sentiment-positive text-xs">최적화됨</Badge>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h4 className="font-medium">유지보수</h4>
                    <div className="space-y-2">
                      <Button variant="outline" className="w-full justify-start">
                        캐시 정리
                      </Button>
                      <Button variant="outline" className="w-full justify-start">
                        로그 다운로드
                      </Button>
                      <Button variant="outline" className="w-full justify-start">
                        시스템 진단
                      </Button>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-border">
                  <div className="space-y-2">
                    <Label htmlFor="backup-note">백업 설정</Label>
                    <Textarea 
                      id="backup-note" 
                      placeholder="자동 백업은 매일 오전 3시에 실행됩니다..."
                      rows={3}
                    />
                  </div>
                </div>
              </CardContent>
            </GlassCard>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}