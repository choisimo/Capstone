---
docsync: true
last_synced: 2025-11-02T13:22:08+0000
source_sha: 6801571a3708f17681de4426d3ea0781fdd5c757
coverage: 1.0
---
# ChangeDetection.io 기반 웹크롤러 모니터링 서비스 PRD

## 1. 제품 개요

### 1.1 제품명
ChangeDetection.io 기반 웹크롤러 모니터링 서비스

### 1.2 목적
ChangeDetection.io API와 AI Agent 기반 크롤링 매크로의 실시간 상태 모니터링 및 제어를 통해 안정적이고 지능적인 데이터 수집 환경을 제공

### 1.3 핵심 혁신점
- **ChangeDetection.io 네이티브 연동**: 웹 변화 감지 전문 서비스 활용
- **AI 매크로 성능 추적**: 자동 생성된 크롤링 매크로의 효율성 모니터링
- **자연어 기반 모니터링**: 사용자가 자연어로 모니터링 요구사항 설정

## 2. 핵심 기능

### 2.1 ChangeDetection.io 연동 모니터링
**기능 설명**: ChangeDetection.io 등록된 모든 워치의 실시간 상태 모니터링
**우선순위**: High
**상세 요구사항**:
- 등록된 워치(Watch) 목록 및 상태 실시간 표시
- 각 워치별 마지막 체크 시간 및 변화 탐지 이력
- API 사용량 및 쿼터 모니터링
- 워치별 성공/실패율 통계
- 응답 시간 및 성능 메트릭
- 웹훅 수신 상태 모니터링

```typescript
interface ChangeDetectionWatch {
  id: string;
  url: string;
  title: string;
  lastChecked: Date;
  lastChanged: Date;
  changeCount: number;
  status: 'active' | 'paused' | 'error' | 'checking';
  checkInterval: number;
  successRate: number;
  avgResponseTime: number;
  tags: string[];
  isAiGenerated: boolean;
}
```

### 2.2 AI 생성 매크로 성능 추적
**기능 설명**: AI Agent가 생성한 크롤링 매크로의 성능 및 효율성 모니터링
**우선순위**: High
**상세 요구사항**:
- AI 매크로별 데이터 추출 성공률
- 매크로 적응성 점수 (사이트 변화 대응력)
- 생성 시간 대비 누적 수집량 효율성
- 에러 패턴 분석 및 자동 개선 제안
- 매크로 버전 관리 및 성능 비교
- 자연어 요구사항 대비 실제 수집 정확도

```typescript
interface AIMacroPerformance {
  macroId: string;
  naturalLanguageRequest: string;
  generatedAt: Date;
  successfulExtractions: number;
  failedExtractions: number;
  adaptationScore: number; // 0-100
  dataQualityScore: number; // 0-100
  performanceMetrics: {
    avgProcessingTime: number;
    dataAccuracy: number;
    siteAdaptability: number;
  };
  lastAdaptation: Date;
  improvementSuggestions: string[];
}
```

### 2.3 실시간 데이터 수집 대시보드
**기능 설명**: 수집되는 데이터의 실시간 현황 및 품질 모니터링
**우선순위**: High
**상세 요구사항**:
- 실시간 데이터 수집 속도 (분당 수집량)
- 소스별 수집 현황 (뉴스, SNS, 블로그 등)
- 데이터 품질 지표 (중복률, 완성도, 정확도)
- 키워드별 수집 트렌드
- 실시간 에러 및 경고 알림
- 수집 데이터 미리보기

### 2.4 지능형 알림 및 에스컬레이션
**기능 설명**: AI 기반 이상 패턴 감지 및 차등 알림 시스템
**우선순위**: High
**상세 요구사항**:
- ChangeDetection.io API 장애 즉시 알림
- AI 매크로 성능 저하 자동 감지
- 데이터 수집량 급변 패턴 알림
- 사이트 구조 변화로 인한 매크로 실패 알림
- 관련자별 맞춤 알림 설정
- 자동 에스컬레이션 워크플로우

### 2.5 자연어 기반 모니터링 설정
**기능 설명**: 사용자가 자연어로 모니터링 규칙을 설정할 수 있는 인터페이스
**우선순위**: Medium
**상세 요구사항**:
- "네이버 뉴스 수집량이 평소보다 50% 줄어들면 알림"
- "AI 매크로 성공률이 80% 이하로 떨어지면 긴급 알림"
- "특정 키워드 수집이 중단되면 담당자에게 SMS 발송"
- 자연어 규칙의 AI 해석 및 검증
- 규칙 효과성 분석 및 개선 제안

## 3. ChangeDetection.io 연동 아키텍처

### 3.1 API 연동 구조
```typescript
class ChangeDetectionIntegration {
  private apiClient: ChangeDetectionClient;

  async syncWatches(): Promise<ChangeDetectionWatch[]> {
    // ChangeDetection.io에서 등록된 모든 워치 동기화
  }

  async handleWebhook(webhookData: WebhookPayload): Promise<void> {
    // 웹훅 수신 시 실시간 처리
  }

  async createAIGeneratedWatch(macro: GeneratedMacro): Promise<string> {
    // AI 생성 매크로를 ChangeDetection.io에 등록
  }

  async updateWatchFromMacro(watchId: string, updatedMacro: GeneratedMacro): Promise<void> {
    // 매크로 업데이트 시 ChangeDetection.io 워치 수정
  }
}

interface WebhookPayload {
  uuid: string;
  watch_url: string;
  current_snapshot: string;
  diff_url: string;
  notification_body: string;
  timestamp: string;
}
```

### 3.2 실시간 모니터링 플로우
```
ChangeDetection.io → Webhook → Processing Queue → AI Analysis → Dashboard Update
        ↓                ↓              ↓              ↓              ↓
   Change Detected → Validation → NLP Processing → Event Generation → User Notification
```

## 4. 사용자 인터페이스

### 4.1 통합 모니터링 대시보드
```typescript
const IntegratedMonitoringDashboard: React.FC = () => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* ChangeDetection.io 상태 */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            ChangeDetection.io 워치 현황
          </CardTitle>
        </CardHeader>
        <CardContent>
          <WatchStatusGrid watches={watches} />
        </CardContent>
      </Card>

      {/* AI 매크로 성능 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            AI 매크로 성능
          </CardTitle>
        </CardHeader>
        <CardContent>
          <AIMacroPerformanceChart />
        </CardContent>
      </Card>

      {/* 실시간 데이터 수집 */}
      <Card className="lg:col-span-3">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            실시간 데이터 수집 현황
          </CardTitle>
        </CardHeader>
        <CardContent>
          <RealTimeCollectionChart />
        </CardContent>
      </Card>
    </div>
  );
};
```

### 4.2 자연어 모니터링 설정 인터페이스
```typescript
const NaturalLanguageMonitoringSetup: React.FC = () => {
  const [nlInput, setNlInput] = useState('');
  const [parsedRule, setParsedRule] = useState<MonitoringRule | null>(null);

  return (
    <Card>
      <CardHeader>
        <CardTitle>자연어 모니터링 규칙 설정</CardTitle>
        <CardDescription>
          자연어로 모니터링 조건을 설정하면 AI가 자동으로 규칙을 생성합니다.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Textarea
          placeholder="예: 네이버 뉴스 수집량이 평소보다 30% 줄어들면 슬랙으로 알림"
          value={nlInput}
          onChange={(e) => setNlInput(e.target.value)}
          className="min-h-[80px]"
        />
        <Button onClick={handleParseRule}>
          AI 규칙 생성
        </Button>
        
        {parsedRule && (
          <div className="mt-4 p-4 border rounded-lg">
            <h4 className="font-semibold mb-2">생성된 모니터링 규칙:</h4>
            <RulePreview rule={parsedRule} />
          </div>
        )}
      </CardContent>
    </Card>
  );
};
```

## 3. 사용자 인터페이스

### 3.1 메인 대시보드
- 크롤러 상태 카드 그리드
- 실시간 메트릭 차트
- 최근 알림 목록
- 빠른 제어 버튼

### 3.2 상세 모니터링 페이지
- 크롤러별 상세 정보
- 히스토리 차트
- 로그 뷰어
- 설정 패널

## 4. 기술 요구사항

### 4.1 성능 요구사항
- 실시간 업데이트 지연 < 3초
- 대시보드 로딩 시간 < 2초
- 동시 사용자 100명 지원

### 4.2 호환성 요구사항
- Chrome, Firefox, Safari 최신 2개 버전
- 모바일 반응형 지원
- 다크모드 지원

## 5. 우선순위 및 일정

### Phase 1 (2주)
- 기본 상태 모니터링
- 수집 통계 차트
- 기본 알림 기능

### Phase 2 (1주)  
- 크롤러 제어 기능
- 상세 모니터링 페이지
- 고급 필터링

### Phase 3 (1주)
- 고급 알림 설정
- 성능 최적화
- 사용자 권한 관리

## 6. 성공 지표

- 시스템 가동률 > 99.5%
- 알림 정확도 > 95%
- 사용자 만족도 > 4.0/5.0
- 응답 시간 < 2초