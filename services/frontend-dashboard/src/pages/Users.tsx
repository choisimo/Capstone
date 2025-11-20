import { useState } from "react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Users as UsersIcon, UserPlus, Search, MoreVertical, Mail, Shield, Clock, Activity } from "lucide-react";

const users = [
  {
    id: 1,
    name: "김정책",
    email: "policy@nps.gov.kr",
    role: "admin",
    department: "정책기획부",
    status: "active",
    lastLogin: "2024-01-07 14:30",
    permissions: ["dashboard_view", "analytics_access", "export_data", "user_management"]
  },
  {
    id: 2,
    name: "이분석",
    email: "analyst@nps.gov.kr",
    role: "analyst",
    department: "데이터분석팀",
    status: "active",
    lastLogin: "2024-01-07 13:45",
    permissions: ["dashboard_view", "analytics_access", "export_data"]
  },
  {
    id: 3,
    name: "박소통",
    email: "comms@nps.gov.kr",
    role: "communications",
    department: "소통협력부",
    status: "active",
    lastLogin: "2024-01-07 12:20",
    permissions: ["dashboard_view", "analytics_access"]
  },
  {
    id: 4,
    name: "최관찰",
    email: "viewer@nps.gov.kr",
    role: "viewer",
    department: "감사부",
    status: "inactive",
    lastLogin: "2024-01-05 16:15",
    permissions: ["dashboard_view"]
  }
];

const rolePermissions = {
  admin: {
    name: "관리자",
    color: "bg-primary/10 text-primary border-primary/20",
    permissions: ["모든 권한", "사용자 관리", "시스템 설정", "데이터 내보내기"]
  },
  analyst: {
    name: "분석가",
    color: "bg-sentiment-positive/10 text-sentiment-positive border-sentiment-positive/20",
    permissions: ["대시보드 조회", "분석 도구", "데이터 내보내기", "리포트 생성"]
  },
  communications: {
    name: "소통담당",
    color: "bg-info/10 text-info border-info/20",
    permissions: ["대시보드 조회", "분석 도구", "이슈 탐색"]
  },
  viewer: {
    name: "조회자",
    color: "bg-muted text-muted-foreground border-muted",
    permissions: ["대시보드 조회만 가능"]
  }
};

export default function Users() {
  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [selectedUser, setSelectedUser] = useState(null);

  const filteredUsers = users.filter(user => {
    if (searchTerm && !user.name.includes(searchTerm) && !user.email.includes(searchTerm)) return false;
    if (roleFilter !== "all" && user.role !== roleFilter) return false;
    if (statusFilter !== "all" && user.status !== statusFilter) return false;
    return true;
  });

  const getRoleBadge = (role: string) => {
    const roleConfig = rolePermissions[role];
    return (
      <Badge className={roleConfig.color}>
        {roleConfig.name}
      </Badge>
    );
  };

  const getStatusBadge = (status: string) => {
    return status === "active" ? (
      <Badge className="bg-sentiment-positive/10 text-sentiment-positive border-sentiment-positive/20">
        활성
      </Badge>
    ) : (
      <Badge variant="secondary">비활성</Badge>
    );
  };

  const getInitials = (name: string) => {
    return name.charAt(0);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <PageHeader
        title="사용자 관리"
        description="시스템 사용자의 권한과 접근을 관리합니다. 역할별로 적절한 권한을 부여하여 보안을 유지합니다."
        badge="관리자 전용"
        actions={
          <Button>
            <UserPlus className="h-4 w-4 mr-2" />
            사용자 추가
          </Button>
        }
      />

      <div className="p-6 space-y-6">
        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <GlassCard className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">전체 사용자</p>
                <p className="text-2xl font-bold">{users.length}</p>
              </div>
              <UsersIcon className="h-8 w-8 text-primary opacity-80" />
            </div>
          </GlassCard>

          <GlassCard className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">활성 사용자</p>
                <p className="text-2xl font-bold">{users.filter(u => u.status === "active").length}</p>
              </div>
              <Activity className="h-8 w-8 text-sentiment-positive opacity-80" />
            </div>
          </GlassCard>

          <GlassCard className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">관리자</p>
                <p className="text-2xl font-bold">{users.filter(u => u.role === "admin").length}</p>
              </div>
              <Shield className="h-8 w-8 text-warning opacity-80" />
            </div>
          </GlassCard>

          <GlassCard className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">최근 로그인</p>
                <p className="text-2xl font-bold">
                  {users.filter(u => {
                    const lastLogin = new Date(u.lastLogin);
                    const now = new Date();
                    const diff = now.getTime() - lastLogin.getTime();
                    return diff < 24 * 60 * 60 * 1000; // 24시간 이내
                  }).length}
                </p>
              </div>
              <Clock className="h-8 w-8 text-info opacity-80" />
            </div>
          </GlassCard>
        </div>

        {/* User Management */}
        <GlassCard>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>사용자 목록</CardTitle>
              <div className="flex items-center gap-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="이름 또는 이메일 검색..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 w-64"
                  />
                </div>
                <Select value={roleFilter} onValueChange={setRoleFilter}>
                  <SelectTrigger className="w-32">
                    <SelectValue placeholder="역할" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">모든 역할</SelectItem>
                    <SelectItem value="admin">관리자</SelectItem>
                    <SelectItem value="analyst">분석가</SelectItem>
                    <SelectItem value="communications">소통담당</SelectItem>
                    <SelectItem value="viewer">조회자</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-32">
                    <SelectValue placeholder="상태" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">모든 상태</SelectItem>
                    <SelectItem value="active">활성</SelectItem>
                    <SelectItem value="inactive">비활성</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>사용자</TableHead>
                  <TableHead>역할</TableHead>
                  <TableHead>부서</TableHead>
                  <TableHead>상태</TableHead>
                  <TableHead>최근 로그인</TableHead>
                  <TableHead className="w-[50px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredUsers.map((user) => (
                  <TableRow key={user.id} className="hover:bg-muted/20">
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <Avatar className="h-8 w-8">
                          <AvatarFallback className="bg-primary/10 text-primary">
                            {getInitials(user.name)}
                          </AvatarFallback>
                        </Avatar>
                        <div>
                          <div className="font-medium">{user.name}</div>
                          <div className="text-sm text-muted-foreground">{user.email}</div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {getRoleBadge(user.role)}
                    </TableCell>
                    <TableCell>
                      <span className="text-sm">{user.department}</span>
                    </TableCell>
                    <TableCell>
                      {getStatusBadge(user.status)}
                    </TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">{user.lastLogin}</span>
                    </TableCell>
                    <TableCell>
                      <Dialog>
                        <DialogTrigger asChild>
                          <Button variant="ghost" size="sm" onClick={() => setSelectedUser(user)}>
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DialogTrigger>
                        <DialogContent className="max-w-2xl">
                          <DialogHeader>
                            <DialogTitle>사용자 상세 정보</DialogTitle>
                          </DialogHeader>
                          
                          {selectedUser && (
                            <Tabs defaultValue="info" className="space-y-4">
                              <TabsList className="grid w-full grid-cols-3">
                                <TabsTrigger value="info">기본 정보</TabsTrigger>
                                <TabsTrigger value="permissions">권한</TabsTrigger>
                                <TabsTrigger value="activity">활동</TabsTrigger>
                              </TabsList>
                              
                              <TabsContent value="info" className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                  <div>
                                    <label className="text-sm font-medium">이름</label>
                                    <Input value={selectedUser.name} readOnly />
                                  </div>
                                  <div>
                                    <label className="text-sm font-medium">이메일</label>
                                    <Input value={selectedUser.email} readOnly />
                                  </div>
                                  <div>
                                    <label className="text-sm font-medium">역할</label>
                                    <Select value={selectedUser.role}>
                                      <SelectTrigger>
                                        <SelectValue />
                                      </SelectTrigger>
                                      <SelectContent>
                                        <SelectItem value="admin">관리자</SelectItem>
                                        <SelectItem value="analyst">분석가</SelectItem>
                                        <SelectItem value="communications">소통담당</SelectItem>
                                        <SelectItem value="viewer">조회자</SelectItem>
                                      </SelectContent>
                                    </Select>
                                  </div>
                                  <div>
                                    <label className="text-sm font-medium">부서</label>
                                    <Input value={selectedUser.department} />
                                  </div>
                                </div>
                              </TabsContent>
                              
                              <TabsContent value="permissions" className="space-y-4">
                                <div className="space-y-3">
                                  <h4 className="font-medium">현재 권한</h4>
                                  {rolePermissions[selectedUser.role].permissions.map((permission, index) => (
                                    <div key={index} className="flex items-center justify-between p-2 rounded border">
                                      <span className="text-sm">{permission}</span>
                                      <Badge variant="outline" className="text-xs">허용됨</Badge>
                                    </div>
                                  ))}
                                </div>
                              </TabsContent>
                              
                              <TabsContent value="activity" className="space-y-4">
                                <div className="space-y-3">
                                  <div className="flex items-center justify-between text-sm">
                                    <span>최근 로그인</span>
                                    <span className="font-mono">{selectedUser.lastLogin}</span>
                                  </div>
                                  <div className="flex items-center justify-between text-sm">
                                    <span>계정 상태</span>
                                    {getStatusBadge(selectedUser.status)}
                                  </div>
                                  <div className="flex items-center justify-between text-sm">
                                    <span>생성일</span>
                                    <span className="font-mono">2023-12-01 09:00</span>
                                  </div>
                                </div>
                              </TabsContent>
                            </Tabs>
                          )}
                        </DialogContent>
                      </Dialog>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </GlassCard>
      </div>
    </div>
  );
}