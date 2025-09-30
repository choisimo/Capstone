---
docsync: true
last_synced: 2025-09-30T01:39:12+0000
source_sha: 6e9c96accdc46e88c87c4fe11f49aa2efddb98d8
coverage: 1.0
---
# 웹크롤러 연동 계획서 (ChangeDetection.io + AI Agent 기반)

## 1. 프로젝트 개요

### 1.1 목적
ChangeDetection.io API와 AI Agent 기반 자동 크롤링 매크로 생성을 통해 국민연금 여론분석 시스템에 지능형 웹 데이터 수집 및 분석 기능을 제공

### 1.2 핵심 기술 스택
- **ChangeDetection.io API**: 웹 페이지 변화 감지 및 기본 크롤링
- **AI Agent**: GPT/Claude 기반 자연어 처리로 크롤링 매크로 자동 생성
- **동적 크롤링**: 사이트 구조 변화에 자동 적응하는 유동적 크롤링

### 1.3 수집 범위
- 뉴스 사이트 (네이버, 다음, 조선일보, 중앙일보 등)
- 소셜미디어 (트위터, 페이스북, 인스타그램)
- 커뮤니티 (네이버 카페, 디시인사이드, 클리앙 등)
- 정부 및 공공기관 웹사이트
- 블로그 플랫폼 (네이버 블로그, 티스토리)

## 2. 기술 아키텍처

### 2.1 전체 시스템 구조
```
Frontend (React) ←→ API Gateway ←→ AI Crawling Orchestrator
                                         ↓
                   ChangeDetection.io API ←→ AI Agent Service
                                         ↓
                   Dynamic Crawler Engine ←→ NLP Processing Service
                                         ↓
                   Data Processing Pipeline ←→ Analytics Service
                                         ↓
                   Real-time Database ←→ Event Detection Engine
```

### 2.2 ChangeDetection.io 연동 구조
```typescript
interface ChangeDetectionConfig {
  apiKey: string;
  baseUrl: 'https://api.changedetection.io';
  watches: {
    id: string;
    url: string;
    tags: string[];
    css_filter?: string;
    xpath_filter?: string;
    trigger_text?: string[];
    headers?: Record<string, string>;
    check_frequency: number; // 초 단위
  }[];
}
```

### 2.3 AI Agent 크롤링 매크로 생성 플로우
```
1. 사용자 자연어 요청 → AI Agent 분석
2. 타겟 사이트 구조 분석 → 크롤링 전략 수립  
3. 매크로 코드 자동 생성 → 테스트 실행
4. 성공 시 ChangeDetection.io 등록 → 모니터링 시작
5. 실패 시 재분석 → 매크로 수정 → 재시도
```

## 3. AI Agent 기반 자동 크롤링 시스템

### 3.1 자연어 처리 인터페이스
**기능**: 사용자가 자연어로 크롤링 요구사항을 입력하면 AI가 자동으로 크롤링 매크로 생성

**예시 입력**:
```
"네이버 뉴스에서 국민연금 관련 기사의 제목, 내용, 댓글을 매일 수집해줘"
"인스타그램에서 #국민연금 해시태그가 있는 포스트들을 실시간으로 모니터링"
"청와대 홈페이지 보도자료 중 연금 관련 내용이 올라오면 즉시 알림"
```

**AI 출력**:
```typescript
interface GeneratedCrawlerConfig {
  target: {
    platform: 'naver_news' | 'instagram' | 'government_site';
    url: string;
    selectors: {
      title: string;
      content: string;
      comments?: string;
      author?: string;
      date: string;
    };
  };
  filters: {
    keywords: string[];
    dateRange?: string;
    hashtags?: string[];
  };
  schedule: {
    frequency: 'realtime' | 'hourly' | 'daily';
    time?: string;
  };
  actions: {
    notify: boolean;
    store: boolean;
    analyze: boolean;
  };
}
```

### 3.2 동적 적응 크롤링
- **DOM 구조 변화 감지**: 사이트 리뉴얼 시 자동 셀렉터 업데이트
- **Anti-bot 우회**: CAPTCHA, 로그인 요구 등 자동 처리
- **로드 밸런싱**: 여러 프록시를 통한 분산 크롤링
- **에러 복구**: 실패 시 다른 전략으로 자동 전환

## 4. 연동 포인트 및 사용자 인터페이스

### 4.1 크롤링 매크로 생성 페이지
- 자연어 입력 텍스트박스
- AI 추천 크롤링 타겟 목록
- 생성된 매크로 미리보기
- 테스트 실행 및 결과 확인
- 일괄 등록 및 스케줄링

### 4.2 실시간 모니터링 대시보드
- ChangeDetection.io 연동 상태
- 활성 크롤링 작업 현황
- AI Agent 생성 매크로 성공률
- 실시간 데이터 수집 통계
- 에러 및 재시도 현황

### 4.3 수집 데이터 탐색 인터페이스
- AI 기반 자연어 검색
- 소스별 데이터 필터링
- 실시간 업데이트 알림
- 중복 제거 및 품질 관리
- 원본 링크 추적

## 5. 단계별 구현 계획

### Phase 1: ChangeDetection.io 기반 인프라 구축 (2주)
- [ ] ChangeDetection.io API 클라이언트 구축
- [ ] 기본 웹 페이지 모니터링 설정
- [ ] 웹훅 수신 시스템 구축
- [ ] 데이터 정규화 및 저장 파이프라인

### Phase 2: AI Agent 크롤링 매크로 생성 시스템 (3주)
- [ ] GPT/Claude API 연동 및 프롬프트 엔지니어링
- [ ] 자연어 요구사항 분석 엔진
- [ ] 크롤링 매크로 자동 생성 로직
- [ ] 생성된 매크로 테스트 및 검증 시스템
- [ ] ChangeDetection.io 자동 등록 기능

### Phase 3: 동적 적응 크롤링 엔진 (3주)
- [ ] DOM 구조 변화 자동 감지
- [ ] 셀렉터 자동 업데이트 알고리즘
- [ ] Anti-bot 우회 전략 구현
- [ ] 프록시 로테이션 및 로드 밸런싱
- [ ] 에러 복구 및 재시도 로직

### Phase 4: 자연어 처리 및 분석 강화 (2주)
- [ ] 한국어 자연어 처리 파이프라인
- [ ] 실시간 감정 분석 및 키워드 추출
- [ ] 토픽 모델링 및 트렌드 분석
- [ ] 중복 제거 및 데이터 품질 관리

### Phase 5: 통합 UI 및 최적화 (2주)
- [ ] 크롤링 매크로 생성 인터페이스
- [ ] 실시간 모니터링 대시보드
- [ ] AI 추천 시스템 UI
- [ ] 성능 최적화 및 스케일링

## 6. 기술 스택 및 API 명세

### 6.1 ChangeDetection.io API 연동
```typescript
// API 클라이언트 구성
class ChangeDetectionClient {
  private apiKey: string;
  private baseUrl = 'https://api.changedetection.io';

  async createWatch(config: WatchConfig): Promise<string> {
    // 새로운 모니터링 대상 등록
  }

  async updateWatch(watchId: string, config: WatchConfig): Promise<void> {
    // 기존 모니터링 설정 업데이트
  }

  async getWatchHistory(watchId: string): Promise<ChangeEvent[]> {
    // 변화 히스토리 조회
  }

  async deleteWatch(watchId: string): Promise<void> {
    // 모니터링 중지 및 삭제
  }
}

interface WatchConfig {
  url: string;
  tag: string[];
  css_filter?: string;
  xpath_filter?: string;
  trigger_text?: string[];
  headers?: Record<string, string>;
  check_frequency: number;
  notification_webhook?: string;
}
```

### 6.2 AI Agent 서비스
```typescript
interface CrawlingRequest {
  naturalLanguageInput: string;
  targetType: 'news' | 'social' | 'blog' | 'government' | 'community';
  urgency: 'realtime' | 'hourly' | 'daily';
  keywords: string[];
}

interface GeneratedMacro {
  id: string;
  description: string;
  targetUrl: string;
  selectors: {
    title: string;
    content: string;
    author?: string;
    date: string;
    comments?: string;
  };
  filters: {
    keywords: string[];
    dateRange?: string;
    excludeKeywords?: string[];
  };
  schedule: {
    frequency: string;
    timezone: string;
  };
  generatedCode: string;
  testResults: {
    success: boolean;
    extractedSample?: any;
    errors?: string[];
  };
}

class AIAgentService {
  async generateCrawlingMacro(request: CrawlingRequest): Promise<GeneratedMacro> {
    // AI를 통한 크롤링 매크로 자동 생성
  }

  async validateMacro(macro: GeneratedMacro): Promise<ValidationResult> {
    // 생성된 매크로 검증 및 테스트
  }

  async adaptToChanges(macroId: string, error: CrawlingError): Promise<GeneratedMacro> {
    // 사이트 변화에 따른 매크로 자동 수정
  }
}
```

### 6.3 자연어 처리 파이프라인
```typescript
interface NLPProcessingResult {
  sentiment: {
    score: number;
    label: 'positive' | 'negative' | 'neutral';
    confidence: number;
  };
  keywords: Array<{
    text: string;
    weight: number;
    category: string;
  }>;
  topics: Array<{
    name: string;
    probability: number;
    keywords: string[];
  }>;
  entities: Array<{
    text: string;
    type: 'PERSON' | 'ORG' | 'LOCATION' | 'POLICY';
    confidence: number;
  }>;
  summary: string;
  language: string;
  trustScore: number;
}

class NLPService {
  async processText(content: string): Promise<NLPProcessingResult> {
    // 한국어 자연어 처리 수행
  }

  async detectDuplicates(contents: string[]): Promise<number[][]> {
    // 중복 콘텐츠 탐지
  }

  async classifyContent(content: string): Promise<string[]> {
    // 콘텐츠 카테고리 분류
  }
}
```

## 7. 프론트엔드 컴포넌트 설계

### 7.1 크롤링 매크로 생성 페이지
```typescript
// src/pages/CrawlerMacroGenerator.tsx
interface CrawlerMacroGeneratorProps {
  onMacroGenerated: (macro: GeneratedMacro) => void;
}

const CrawlerMacroGenerator: React.FC<CrawlerMacroGeneratorProps> = () => {
  const [naturalLanguageInput, setNaturalLanguageInput] = useState('');
  const [generatedMacro, setGeneratedMacro] = useState<GeneratedMacro | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>AI 크롤링 매크로 생성</CardTitle>
          <CardDescription>
            자연어로 크롤링 요구사항을 입력하면 AI가 자동으로 매크로를 생성합니다.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Textarea
            placeholder="예: 네이버 뉴스에서 국민연금 관련 기사를 매일 수집해주세요"
            value={naturalLanguageInput}
            onChange={(e) => setNaturalLanguageInput(e.target.value)}
            className="min-h-[100px]"
          />
          <Button 
            onClick={handleGenerateMacro}
            disabled={isGenerating}
            className="mt-4"
          >
            {isGenerating ? '생성 중...' : 'AI 매크로 생성'}
          </Button>
        </CardContent>
      </Card>

      {generatedMacro && (
        <MacroPreviewCard 
          macro={generatedMacro}
          onTest={handleTestMacro}
          onDeploy={handleDeployMacro}
        />
      )}
    </div>
  );
};
```

### 7.2 실시간 크롤링 모니터링 대시보드
```typescript
// src/components/dashboard/CrawlingMonitorDashboard.tsx
const CrawlingMonitorDashboard: React.FC = () => {
  const { data: crawlingStats } = useQuery({
    queryKey: ['crawling-stats'],
    queryFn: fetchCrawlingStats,
    refetchInterval: 5000, // 5초마다 업데이트
  });

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricCard
        title="활성 크롤러"
        value={crawlingStats?.activeCrawlers || 0}
        change={crawlingStats?.crawlerChange}
        icon={Activity}
      />
      <MetricCard
        title="오늘 수집량"
        value={crawlingStats?.todayCollected || 0}
        change={crawlingStats?.collectionChange}
        icon={Download}
      />
      <MetricCard
        title="AI 매크로 성공률"
        value={`${crawlingStats?.aiSuccessRate || 0}%`}
        change={crawlingStats?.successRateChange}
        icon={Brain}
      />
      <MetricCard
        title="실시간 처리량"
        value={`${crawlingStats?.realtimeRate || 0}/분`}
        change={crawlingStats?.rateChange}
        icon={Zap}
      />
    </div>
  );
};
```

## 8. 리스크 및 대응 방안

### 8.1 기술적 리스크
- **ChangeDetection.io API 제한**: 백업 크롤링 서비스 준비
- **AI 매크로 생성 실패**: 수동 매크로 생성 폴백 제공
- **사이트 구조 변화**: 자동 적응 알고리즘 및 알림 시스템
- **대용량 데이터 처리**: 스트리밍 및 배치 처리 하이브리드 구조
- **자연어 처리 정확도**: 지속적인 모델 학습 및 피드백 루프

### 8.2 법적/윤리적 리스크
- **robots.txt 준수**: 자동 검증 시스템 구축
- **개인정보 보호**: 민감 정보 자동 마스킹
- **저작권 이슈**: 페어 유즈 가이드라인 준수
- **API 사용 약관**: ChangeDetection.io 이용약관 모니터링

### 8.3 운영 리스크
- **서비스 의존성**: ChangeDetection.io 장애 시 대응 계획
- **비용 관리**: API 사용량 모니터링 및 예산 관리
- **데이터 품질**: 자동 품질 검증 및 필터링
- **확장성**: 마이크로서비스 아키텍처 기반 설계

## 9. 성공 지표

### 9.1 기술적 지표
- AI 매크로 생성 성공률 > 85%
- 크롤링 데이터 정확도 > 90%
- 실시간 처리 지연 < 30초
- 시스템 가동률 > 99.5%
- API 응답 시간 < 3초

### 9.2 비즈니스 지표
- 데이터 수집 범위 확장 > 200%
- 이슈 탐지 시간 단축 > 70%
- 사용자 만족도 > 4.2/5.0
- 수동 작업 감소 > 80%
- ROI > 300% (1년 내)

## 10. 예상 비용 및 리소스

### 10.1 ChangeDetection.io 비용
- 기본 플랜: $39/월 (100개 모니터링)
- 프로 플랜: $89/월 (1000개 모니터링)
- 엔터프라이즈: 커스텀 가격

### 10.2 AI API 비용 (월간 예상)
- GPT-4 API: $500-1000 (매크로 생성용)
- Claude API: $300-600 (백업 및 검증용)
- 한국어 NLP API: $200-400

### 10.3 인프라 비용
- 서버 및 데이터베이스: $300-500/월
- CDN 및 스토리지: $100-200/월
- 모니터링 및 로깅: $50-100/월

## 11. 다음 단계

### 11.1 즉시 실행 (1주 내)
1. **ChangeDetection.io 계정 생성 및 API 키 발급**
2. **AI API 계정 설정 (OpenAI, Anthropic)**
3. **프로토타입 개발 환경 구축**
4. **기본 API 연동 테스트**

### 11.2 단기 목표 (1개월 내)
1. **MVP 크롤링 매크로 생성 시스템 구축**
2. **5-10개 주요 뉴스 사이트 자동 모니터링**
3. **기본 자연어 처리 파이프라인 구축**
4. **실시간 데이터 수집 및 저장 시스템**

### 11.3 중기 목표 (3개월 내)
1. **100+ 사이트 자동 크롤링 시스템**
2. **고도화된 AI 매크로 생성 엔진**
3. **완전 자동화된 모니터링 대시보드**
4. **통합 분석 및 알림 시스템**

### 11.4 장기 목표 (6개월 내)
1. **멀티모달 데이터 수집 (이미지, 비디오)**
2. **예측 분석 및 트렌드 포캐스팅**
3. **크로스 플랫폼 여론 분석**
4. **자동 정책 제안 시스템**