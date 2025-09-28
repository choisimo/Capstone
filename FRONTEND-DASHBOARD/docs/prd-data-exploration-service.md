---
docsync: true
last_synced: 2025-09-29T01:02:34+0900
source_sha: af745df9851adc5c9bb20a05c6f65b6905f0ed33
coverage: 1.0
---
# AI 기반 데이터 수집 및 탐색 서비스 PRD

## 1. 제품 개요

### 1.1 제품명
AI 기반 데이터 수집 및 탐색 서비스 (AI-Powered Data Collection & Exploration Service)

### 1.2 목적
ChangeDetection.io와 AI Agent로 수집된 대용량 다양성 데이터를 지능적으로 탐색하고 분석할 수 있는 차세대 통합 인터페이스 제공

### 1.3 핵심 혁신점
- **AI 기반 자연어 검색**: 복잡한 쿼리를 자연어로 간단하게 표현
- **실시간 수집 데이터 통합**: ChangeDetection.io 웹훅과 AI 매크로 데이터 실시간 동기화
- **지능형 데이터 품질 관리**: AI 기반 중복 제거 및 신뢰도 평가
- **맥락적 데이터 연결**: 관련 데이터 자동 발견 및 연결

### 1.4 대상 사용자
- 정책 분석가 (자연어 검색 선호)
- 연구원 (정밀한 데이터 분석 필요)
- 데이터 분석가 (고급 필터링 및 API 접근)
- 관리자 (데이터 품질 및 권한 관리)

## 2. 핵심 기능

### 2.1 AI 기반 자연어 검색 시스템
**기능 설명**: 자연어 질의를 구조화된 검색 쿼리로 자동 변환
**우선순위**: High
**상세 요구사항**:
- 복잡한 검색 조건을 자연어로 표현
- 의도 분석 및 쿼리 최적화
- 검색 결과 설명 및 근거 제시
- 검색 히스토리 및 즐겨찾기 관리
- 음성 검색 지원 (향후)

**자연어 검색 예시**:
```
입력: "지난 일주일 동안 네이버 뉴스에서 국민연금 수급나이 상향에 대한 부정적 반응이 많은 기사들을 보여줘"

AI 해석:
- 기간: 7일 전 ~ 현재
- 소스: 네이버 뉴스
- 키워드: ["국민연금", "수급나이", "상향"]
- 감정: 부정적 (sentiment < -0.3)
- 정렬: 부정적 반응 많은 순

생성된 쿼리:
{
  "dateRange": {"start": "2024-01-08", "end": "2024-01-15"},
  "source": "naver_news",
  "keywords": ["국민연금", "수급나이", "상향"],
  "sentiment": {"max": -0.3},
  "sortBy": "negative_sentiment_score",
  "includeComments": true
}
```

### 2.2 실시간 AI 수집 데이터 통합
**기능 설명**: ChangeDetection.io와 AI 매크로에서 수집된 데이터의 실시간 통합 및 정규화
**우선순위**: High
**상세 요구사항**:
- ChangeDetection.io 웹훅 실시간 처리
- AI 생성 매크로 데이터 자동 통합
- 중복 데이터 지능형 탐지 및 병합
- 데이터 소스 추적 및 신뢰도 평가
- 실시간 데이터 품질 모니터링

```typescript
interface UnifiedDataEntry {
  id: string;
  originalSource: 'changedetection' | 'ai_macro' | 'manual';
  collectionMethod: {
    service: string;
    macroId?: string;
    watchId?: string;
    confidence: number;
  };
  content: {
    title: string;
    body: string;
    url: string;
    author?: string;
    publishedAt: Date;
    collectedAt: Date;
  };
  analysis: {
    sentiment: SentimentAnalysis;
    keywords: ExtractedKeyword[];
    topics: TopicAnalysis[];
    entities: NamedEntity[];
    trustScore: number;
    qualityScore: number;
  };
  metadata: {
    platform: string;
    contentType: string;
    language: string;
    duplicateIds: string[];
    relatedIds: string[];
  };
}
```

### 2.3 지능형 고급 필터링 시스템
**기능 설명**: AI 보조 기반 다차원 필터 및 동적 필터 추천
**우선순위**: High
**상세 요구사항**:
- AI 추천 필터 조합
- 동적 필터 값 자동 완성
- 필터 간 연관성 분석 및 제안
- 저장된 필터 세트 관리
- 필터 성능 분석 및 최적화

**지능형 필터 기능**:
- **스마트 키워드 확장**: "국민연금" → ["국민연금", "NPS", "공적연금", "노령연금"]
- **연관 키워드 제안**: "수급나이" 검색 시 → "정년연장", "조기수급", "연금개혁" 제안
- **감정 기반 필터링**: "논란이 된 내용만" → sentiment < -0.5 && engagement > 평균*2
- **시간적 패턴 필터**: "이슈가 확산되는 시점" → 언급량 급증 구간 자동 감지

### 2.4 AI 기반 데이터 상세 분석
**기능 설명**: 선택된 데이터에 대한 AI 보강 분석 및 인사이트 제공
**우선순위**: High
**상세 요구사항**:
- 콘텐츠 요약 및 핵심 포인트 추출
- 관련 데이터 자동 발견 및 연결
- 팩트 체킹 및 신뢰도 검증
- 시간별 여론 변화 추적
- 영향력 및 확산 경로 분석

```typescript
interface AIEnhancedAnalysis {
  summary: {
    keyPoints: string[];
    mainArguments: string[];
    stakeholders: string[];
    timeline: TimelineEvent[];
  };
  factCheck: {
    claims: Array<{
      statement: string;
      verification: 'verified' | 'disputed' | 'unverified';
      sources: string[];
      confidence: number;
    }>;
  };
  relatedContent: {
    similarArticles: RelatedContent[];
    followUpStories: RelatedContent[];
    contradictingViews: RelatedContent[];
  };
  impactAnalysis: {
    viralityScore: number;
    influenceNetwork: InfluenceNode[];
    geographicSpread: GeographicData[];
    demographicBreakdown: DemographicData[];
  };
}
```

### 2.5 실시간 협업 및 공유 기능
**기능 설명**: 팀 기반 데이터 탐색 및 인사이트 공유
**우선순위**: Medium
**상세 요구사항**:
- 실시간 검색 결과 공유
- 팀 워크스페이스 및 대시보드
- 어노테이션 및 댓글 시스템
- 알림 및 멘션 기능
- 권한 기반 접근 제어

### 2.6 지능형 데이터 내보내기
**기능 설명**: AI 보조 기반 맞춤형 데이터 내보내기
**우선순위**: Medium
**상세 요구사항**:
- 목적별 최적화된 내보내기 형식 추천
- 자동 데이터 요약 및 인사이트 첨부
- 시각화 차트 자동 생성 및 포함
- 예약 리포트 자동 생성
- API 기반 실시간 데이터 피드

## 3. AI 기반 검색 아키텍처

### 3.1 자연어 쿼리 처리 파이프라인
```typescript
class NLQueryProcessor {
  async processQuery(naturalLanguageQuery: string): Promise<StructuredQuery> {
    // 1. 의도 분석
    const intent = await this.analyzeIntent(naturalLanguageQuery);
    
    // 2. 개체명 인식
    const entities = await this.extractEntities(naturalLanguageQuery);
    
    // 3. 시간 표현 파싱
    const timeExpressions = await this.parseTimeExpressions(naturalLanguageQuery);
    
    // 4. 감정/태도 분석
    const attitudeFilters = await this.analyzeAttitude(naturalLanguageQuery);
    
    // 5. 구조화된 쿼리 생성
    return this.buildStructuredQuery(intent, entities, timeExpressions, attitudeFilters);
  }

  async suggestQueryRefinements(query: string, results: SearchResult[]): Promise<string[]> {
    // 검색 결과 기반 쿼리 개선 제안
  }
}

interface StructuredQuery {
  intent: 'search' | 'monitor' | 'analyze' | 'compare';
  filters: {
    keywords: KeywordFilter[];
    dateRange?: DateRange;
    sources?: string[];
    sentiment?: SentimentFilter;
    engagement?: EngagementFilter;
    geography?: GeographyFilter;
  };
  aggregations?: {
    groupBy: string[];
    metrics: string[];
    timeGranularity?: string;
  };
  sort: SortCriteria[];
  limit?: number;
}
```

### 3.2 실시간 데이터 동기화
```typescript
class RealTimeDataSync {
  private changeDetectionHandler: ChangeDetectionWebhookHandler;
  private aiMacroDataHandler: AIMacroDataHandler;

  async handleChangeDetectionWebhook(webhook: ChangeDetectionWebhook): Promise<void> {
    // 1. 웹훅 데이터 검증
    const validatedData = await this.validateWebhookData(webhook);
    
    // 2. 콘텐츠 추출 및 정규화
    const extractedContent = await this.extractContent(validatedData);
    
    // 3. AI 분석 (감정, 키워드, 주제 등)
    const aiAnalysis = await this.performAIAnalysis(extractedContent);
    
    // 4. 중복 검사 및 데이터 통합
    const deduplicatedData = await this.deduplicateData(extractedContent, aiAnalysis);
    
    // 5. 실시간 인덱싱
    await this.indexData(deduplicatedData);
    
    // 6. 실시간 알림 발송
    await this.notifyRelevantUsers(deduplicatedData);
  }

  async handleAIMacroData(macroResult: AIMacroResult): Promise<void> {
    // AI 매크로 수집 데이터 처리
  }
}
```

## 4. 사용자 인터페이스 설계

### 4.1 지능형 검색 인터페이스
```typescript
const IntelligentSearchInterface: React.FC = () => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [structuredQuery, setStructuredQuery] = useState<StructuredQuery | null>(null);
  
  return (
    <div className="space-y-6">
      {/* AI 자연어 검색바 */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
            <Textarea
              placeholder="자연어로 검색하세요. 예: 지난 주 국민연금 관련 부정적 기사들"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-10 min-h-[60px] resize-none"
            />
            <div className="absolute right-3 top-3 flex gap-2">
              <Button size="sm" variant="ghost">
                <Mic className="h-4 w-4" />
              </Button>
              <Button size="sm">
                <Brain className="h-4 w-4 mr-1" />
                AI 검색
              </Button>
            </div>
          </div>
          
          {/* AI 해석 미리보기 */}
          {structuredQuery && (
            <div className="mt-4 p-3 bg-muted rounded-lg">
              <div className="text-sm font-medium mb-2">AI 검색 해석:</div>
              <QueryInterpretationPreview query={structuredQuery} />
            </div>
          )}
        </CardContent>
      </Card>

      {/* 추천 검색어 */}
      <div className="flex flex-wrap gap-2">
        {suggestions.map((suggestion, index) => (
          <Badge 
            key={index} 
            variant="outline" 
            className="cursor-pointer hover:bg-primary hover:text-primary-foreground"
            onClick={() => setQuery(suggestion)}
          >
            {suggestion}
          </Badge>
        ))}
      </div>
    </div>
  );
};
```

### 4.2 실시간 데이터 스트림 대시보드
```typescript
const RealTimeDataStream: React.FC = () => {
  const { data: liveData, isConnected } = useWebSocket('/api/live-data-stream');
  
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Radio className="h-5 w-5" />
            실시간 데이터 수집
          </CardTitle>
          <Badge variant={isConnected ? "success" : "destructive"}>
            {isConnected ? "연결됨" : "연결 끊김"}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* 실시간 수집 통계 */}
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {liveData?.collectionsPerMinute || 0}
              </div>
              <div className="text-sm text-muted-foreground">분당 수집</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {liveData?.activeSources || 0}
              </div>
              <div className="text-sm text-muted-foreground">활성 소스</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {liveData?.aiMacrosRunning || 0}
              </div>
              <div className="text-sm text-muted-foreground">AI 매크로</div>
            </div>
          </div>

          {/* 실시간 데이터 피드 */}
          <div className="max-h-64 overflow-y-auto space-y-2">
            {liveData?.recentEntries?.map((entry, index) => (
              <RealTimeDataEntry key={index} entry={entry} />
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
```

### 4.3 AI 분석 결과 표시
```typescript
const AIAnalysisResults: React.FC<{ data: UnifiedDataEntry }> = ({ data }) => {
  return (
    <Tabs defaultValue="summary" className="w-full">
      <TabsList className="grid w-full grid-cols-5">
        <TabsTrigger value="summary">요약</TabsTrigger>
        <TabsTrigger value="sentiment">감정분석</TabsTrigger>
        <TabsTrigger value="related">연관데이터</TabsTrigger>
        <TabsTrigger value="fact-check">팩트체크</TabsTrigger>
        <TabsTrigger value="impact">영향분석</TabsTrigger>
      </TabsList>

      <TabsContent value="summary" className="space-y-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              AI 생성 요약
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div>
                <h4 className="font-medium mb-2">핵심 포인트</h4>
                <ul className="list-disc list-inside space-y-1">
                  {data.analysis.summary?.keyPoints.map((point, index) => (
                    <li key={index} className="text-sm">{point}</li>
                  ))}
                </ul>
              </div>
              
              <div>
                <h4 className="font-medium mb-2">주요 이해관계자</h4>
                <div className="flex flex-wrap gap-2">
                  {data.analysis.summary?.stakeholders.map((stakeholder, index) => (
                    <Badge key={index} variant="outline">{stakeholder}</Badge>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="sentiment">
        <SentimentAnalysisChart data={data.analysis.sentiment} />
      </TabsContent>

      <TabsContent value="related">
        <RelatedContentGrid data={data.analysis.relatedContent} />
      </TabsContent>

      <TabsContent value="fact-check">
        <FactCheckResults data={data.analysis.factCheck} />
      </TabsContent>

      <TabsContent value="impact">
        <ImpactAnalysisVisualization data={data.analysis.impactAnalysis} />
      </TabsContent>
    </Tabs>
  );
};
```

## 3. 사용자 인터페이스

### 3.1 탐색 메인 페이지
- 통합 검색바
- 빠른 필터 버튼
- 최근 검색 목록
- 인기 키워드
- 실시간 피드 미리보기

### 3.2 검색 결과 페이지
- 검색 결과 리스트 (무한 스크롤)
- 사이드바 필터 패널
- 정렬 옵션
- 결과 개수 표시
- 저장된 검색 관리

### 3.3 데이터 상세 페이지
- 콘텐츠 본문 표시
- 메타데이터 패널
- 관련 문서 추천
- 태그 및 카테고리
- 공유 및 북마크 기능

### 3.4 내보내기 페이지
- 내보내기 설정 패널
- 미리보기 기능
- 진행 상황 표시
- 다운로드 히스토리

## 4. 기술 요구사항

### 4.1 성능 요구사항
- 검색 응답 시간 < 2초
- 대용량 데이터 (1M+ 건) 처리 지원
- 가상화를 통한 메모리 효율성
- 무한 스크롤 최적화

### 4.2 데이터 요구사항
- 실시간 데이터 동기화
- 데이터 무결성 보장
- 백업 및 복구 지원
- 데이터 아카이빙

### 4.3 보안 요구사항
- 사용자 권한 기반 접근 제어
- 민감 정보 마스킹
- 감사 로그 기록
- 데이터 암호화

## 5. 데이터 스키마

### 5.1 수집 데이터 구조
```typescript
interface CollectedData {
  id: string;
  title: string;
  content: string;
  source: 'news' | 'blog' | 'sns' | 'forum';
  url: string;
  author?: string;
  publishedAt: Date;
  collectedAt: Date;
  sentiment: {
    score: number;
    label: 'positive' | 'negative' | 'neutral';
    confidence: number;
  };
  keywords: string[];
  category: string;
  trustScore: number;
  metadata: Record<string, any>;
}
```

### 5.2 검색 필터 구조
```typescript
interface SearchFilter {
  query?: string;
  dateRange?: {
    start: Date;
    end: Date;
  };
  sources?: string[];
  sentiments?: string[];
  keywords?: string[];
  trustScoreRange?: {
    min: number;
    max: number;
  };
  categories?: string[];
}
```

## 6. 우선순위 및 일정

### Phase 1 (3주)
- 통합 검색 인터페이스
- 기본 필터링 시스템
- 데이터 상세 보기
- 검색 결과 페이지

### Phase 2 (2주)
- 고급 필터링 기능
- 실시간 데이터 스트림
- 성능 최적화
- 가상화 구현

### Phase 3 (1주)
- 데이터 내보내기 기능
- 사용자 설정 저장
- 고급 검색 옵션
- 접근 권한 관리

## 7. 성공 지표

- 검색 정확도 > 90%
- 사용자 재방문율 > 70%
- 데이터 활용률 > 80%
- 검색 응답 시간 < 2초
- 사용자 만족도 > 4.5/5.0

## 8. 위험 요소 및 대응방안

### 8.1 기술적 위험
- **대용량 데이터 처리**: 가상화 및 페이지네이션 구현
- **검색 성능**: 인덱싱 최적화 및 캐싱 전략
- **실시간 업데이트**: WebSocket 연결 안정성 확보

### 8.2 사용성 위험
- **복잡한 UI**: 단계적 기능 공개 및 튜토리얼 제공
- **검색 결과 품질**: 머신러닝 기반 랭킹 알고리즘 적용
- **데이터 신뢰성**: 소스 신뢰도 점수 시스템 구축