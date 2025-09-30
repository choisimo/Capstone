---
docsync: true
last_synced: 2025-09-30T08:38:26+0900
source_sha: 733a9bd12e34e77d0e4054796389a7477c15b29d
coverage: 1.0
---
# AI Agent 크롤링 매크로 생성 서비스 PRD

## 1. 제품 개요

### 1.1 제품명
AI Agent 크롤링 매크로 생성 서비스 (AI Agent Crawling Macro Generation Service)

### 1.2 목적
자연어 처리와 AI Agent 기술을 활용하여 사용자의 자연어 요구사항을 자동으로 크롤링 매크로로 변환하고, 웹사이트 구조 변화에 자동 적응하는 지능형 크롤링 시스템 제공

### 1.3 핵심 혁신점
- **Zero-Code 크롤링**: 코딩 지식 없이 자연어로 크롤링 요구사항 설정
- **자동 적응**: 웹사이트 구조 변화 시 매크로 자동 업데이트
- **지능형 데이터 추출**: AI 기반 콘텐츠 이해 및 정확한 정보 추출

## 2. 핵심 기능

### 2.1 자연어 요구사항 분석 엔진
**기능 설명**: 사용자의 자연어 입력을 분석하여 크롤링 요구사항을 구조화
**우선순위**: High
**상세 요구사항**:
- 한국어 자연어 처리 (NLP) 엔진
- 의도 분류 (Intent Classification)
- 개체명 인식 (Named Entity Recognition)
- 요구사항 검증 및 명확화 제안
- 모호한 요청에 대한 질문 생성

**입력 예시**:
```
"네이버 뉴스에서 국민연금 관련 기사 제목과 내용을 매일 오전 9시에 수집해주세요"
"인스타그램에서 #국민연금 해시태그가 포함된 포스트를 실시간으로 모니터링"
"청와대 보도자료 중 연금 정책 관련 내용이 업데이트되면 즉시 알림"
```

**출력 구조**:
```typescript
interface ParsedCrawlingRequest {
  intent: 'data_collection' | 'monitoring' | 'notification';
  target: {
    platform: string;
    url?: string;
    section?: string;
  };
  dataTypes: string[]; // ['title', 'content', 'author', 'date', 'comments']
  filters: {
    keywords: string[];
    hashtags?: string[];
    dateRange?: string;
    excludeTerms?: string[];
  };
  schedule: {
    frequency: 'realtime' | 'hourly' | 'daily' | 'weekly';
    time?: string;
    timezone?: string;
  };
  actions: {
    store: boolean;
    notify: boolean;
    analyze: boolean;
  };
  confidence: number; // 0-1
  clarificationQuestions?: string[];
}
```

### 2.2 지능형 매크로 생성 엔진
**기능 설명**: 분석된 요구사항을 기반으로 실행 가능한 크롤링 매크로 자동 생성
**우선순위**: High
**상세 요구사항**:
- GPT-4/Claude 기반 코드 생성
- 웹사이트별 최적화된 크롤링 전략 선택
- CSS/XPath 셀렉터 자동 생성
- Anti-bot 우회 전략 포함
- 에러 처리 및 재시도 로직 자동 삽입

```typescript
interface GeneratedCrawlingMacro {
  id: string;
  description: string;
  originalRequest: string;
  targetConfig: {
    url: string;
    platform: string;
    authentication?: {
      required: boolean;
      method?: 'cookie' | 'token' | 'login';
    };
  };
  extractionRules: {
    selectors: Record<string, string>; // fieldName -> CSS/XPath selector
    fallbackSelectors: Record<string, string[]>;
    dataValidation: Record<string, string>; // field -> validation regex
  };
  generatedCode: {
    language: 'python' | 'javascript';
    code: string;
    dependencies: string[];
  };
  testResults: {
    success: boolean;
    extractedSample?: Record<string, any>;
    errors?: string[];
    performance?: {
      executionTime: number;
      memoryUsage: number;
    };
  };
  adaptationCapability: {
    robustnessScore: number; // 0-100
    fallbackStrategies: string[];
    changeDetectionMethod: string;
  };
}
```

### 2.3 동적 사이트 적응 시스템
**기능 설명**: 웹사이트 구조 변화를 자동 감지하고 매크로를 업데이트
**우선순위**: High
**상세 요구사항**:
- DOM 구조 변화 자동 감지
- 셀렉터 자동 재계산 및 업데이트
- A/B 테스트 및 동적 콘텐츠 대응
- 실패 시 AI 기반 재분석 및 매크로 재생성
- 사이트 업데이트 패턴 학습

```typescript
interface AdaptationEngine {
  async detectChanges(siteUrl: string, lastSnapshot: string): Promise<ChangeDetectionResult>;
  async regenerateSelectors(macro: GeneratedCrawlingMacro, changes: ChangeDetectionResult): Promise<UpdatedMacro>;
  async testAdaptedMacro(macro: UpdatedMacro): Promise<ValidationResult>;
  async learnFromFailure(macro: GeneratedCrawlingMacro, error: CrawlingError): Promise<ImprovedMacro>;
}

interface ChangeDetectionResult {
  structuralChanges: boolean;
  addedElements: string[];
  removedElements: string[];
  modifiedElements: string[];
  confidence: number;
  adaptationStrategy: 'minor_update' | 'major_regeneration' | 'manual_review_required';
}
```

### 2.4 매크로 성능 최적화
**기능 설명**: 생성된 매크로의 성능을 지속적으로 모니터링하고 최적화
**우선순위**: Medium
**상세 요구사항**:
- 실행 시간 최적화
- 메모리 사용량 최소화
- 네트워크 요청 효율화
- 배치 처리 vs 실시간 처리 최적 선택
- 사이트별 최적 요청 간격 학습

### 2.5 매크로 템플릿 라이브러리
**기능 설명**: 주요 사이트별 최적화된 매크로 템플릿 제공
**우선순위**: Medium
**상세 요구사항**:
- 네이버, 다음, 구글 등 주요 플랫폼 템플릿
- 뉴스, SNS, 커뮤니티별 특화 템플릿
- 사용자 생성 템플릿 공유 시스템
- 템플릿 버전 관리 및 업데이트
- 성능 기반 템플릿 랭킹

## 3. AI Agent 아키텍처

### 3.1 멀티 에이전트 시스템
```typescript
interface AIAgentOrchestrator {
  nlpAgent: NLPAnalysisAgent;
  codeGenAgent: CodeGenerationAgent;
  testAgent: ValidationAgent;
  adaptationAgent: AdaptationAgent;
  optimizationAgent: OptimizationAgent;
}

class NLPAnalysisAgent {
  async analyzeRequest(naturalLanguageInput: string): Promise<ParsedCrawlingRequest>;
  async generateClarificationQuestions(ambiguousRequest: string): Promise<string[]>;
  async validateParsedIntent(parsed: ParsedCrawlingRequest): Promise<ValidationResult>;
}

class CodeGenerationAgent {
  async generateMacro(request: ParsedCrawlingRequest): Promise<GeneratedCrawlingMacro>;
  async optimizeCode(macro: GeneratedCrawlingMacro): Promise<OptimizedMacro>;
  async addErrorHandling(macro: GeneratedCrawlingMacro): Promise<RobustMacro>;
}

class AdaptationAgent {
  async monitorSiteChanges(url: string): Promise<ChangeEvent[]>;
  async adaptMacro(macro: GeneratedCrawlingMacro, changes: ChangeEvent[]): Promise<AdaptedMacro>;
  async learnFromAdaptations(adaptationHistory: AdaptationEvent[]): Promise<LearningInsights>;
}
```

### 3.2 프롬프트 엔지니어링 시스템
```typescript
interface PromptTemplate {
  name: string;
  description: string;
  template: string;
  variables: string[];
  examples: Array<{
    input: Record<string, any>;
    expectedOutput: string;
  }>;
}

class PromptEngine {
  private templates: Map<string, PromptTemplate>;

  async generateCrawlingCode(request: ParsedCrawlingRequest): Promise<string> {
    const prompt = this.buildPrompt('crawling_code_generation', {
      platform: request.target.platform,
      dataTypes: request.dataTypes,
      filters: request.filters,
      schedule: request.schedule
    });
    
    return await this.aiClient.generateCode(prompt);
  }

  async adaptMacroCode(macro: GeneratedCrawlingMacro, error: CrawlingError): Promise<string> {
    const prompt = this.buildPrompt('macro_adaptation', {
      originalCode: macro.generatedCode.code,
      error: error.message,
      siteChanges: error.detectedChanges
    });
    
    return await this.aiClient.generateCode(prompt);
  }
}
```

## 4. 사용자 인터페이스

### 4.1 매크로 생성 위저드
```typescript
const MacroGenerationWizard: React.FC = () => {
  const [step, setStep] = useState(1);
  const [nlInput, setNlInput] = useState('');
  const [parsedRequest, setParsedRequest] = useState<ParsedCrawlingRequest | null>(null);
  const [generatedMacro, setGeneratedMacro] = useState<GeneratedCrawlingMacro | null>(null);

  return (
    <div className="max-w-4xl mx-auto">
      <Steps current={step} className="mb-8">
        <Step title="요구사항 입력" description="자연어로 크롤링 요구사항 작성" />
        <Step title="의도 확인" description="AI가 분석한 요구사항 검토" />
        <Step title="매크로 생성" description="AI가 자동으로 크롤링 매크로 생성" />
        <Step title="테스트 및 배포" description="생성된 매크로 테스트 및 배포" />
      </Steps>

      {step === 1 && (
        <NaturalLanguageInput 
          value={nlInput}
          onChange={setNlInput}
          onNext={() => setStep(2)}
          examples={[
            "네이버 뉴스에서 국민연금 관련 기사를 매일 수집",
            "인스타그램 #국민연금 해시태그 실시간 모니터링",
            "정부 보도자료 중 연금 정책 관련 내용 자동 수집"
          ]}
        />
      )}

      {step === 2 && parsedRequest && (
        <IntentConfirmation 
          parsed={parsedRequest}
          onConfirm={() => setStep(3)}
          onEdit={() => setStep(1)}
        />
      )}

      {step === 3 && (
        <MacroGeneration
          request={parsedRequest}
          onGenerated={setGeneratedMacro}
          onNext={() => setStep(4)}
        />
      )}

      {step === 4 && generatedMacro && (
        <MacroTestAndDeploy
          macro={generatedMacro}
          onDeploy={handleDeploy}
        />
      )}
    </div>
  );
};
```

### 4.2 매크로 관리 대시보드
```typescript
const MacroManagementDashboard: React.FC = () => {
  const { data: macros } = useQuery({
    queryKey: ['user-macros'],
    queryFn: fetchUserMacros,
  });

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">크롤링 매크로 관리</h1>
        <Button onClick={() => navigate('/create-macro')}>
          <Plus className="mr-2 h-4 w-4" />
          새 매크로 생성
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {macros?.map(macro => (
          <MacroCard
            key={macro.id}
            macro={macro}
            onEdit={handleEdit}
            onDelete={handleDelete}
            onToggle={handleToggle}
          />
        ))}
      </div>

      <MacroPerformanceChart macros={macros} />
    </div>
  );
};

const MacroCard: React.FC<{ macro: GeneratedCrawlingMacro }> = ({ macro }) => {
  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between items-start">
          <CardTitle className="text-sm font-medium">{macro.description}</CardTitle>
          <Badge variant={macro.testResults.success ? 'success' : 'destructive'}>
            {macro.testResults.success ? '활성' : '오류'}
          </Badge>
        </div>
        <CardDescription className="text-xs">
          {macro.originalRequest}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>성공률:</span>
            <span>{macro.adaptationCapability.robustnessScore}%</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>마지막 실행:</span>
            <span>{format(new Date(), 'MM/dd HH:mm')}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span>수집량:</span>
            <span>1,234건</span>
          </div>
        </div>
      </CardContent>
      <CardFooter className="gap-2">
        <Button size="sm" variant="outline">편집</Button>
        <Button size="sm" variant="outline">테스트</Button>
        <Button size="sm">상세보기</Button>
      </CardFooter>
    </Card>
  );
};
```

## 5. 기술 스택 및 의존성

### 5.1 AI/ML 서비스
- **OpenAI GPT-4**: 코드 생성 및 자연어 처리
- **Anthropic Claude**: 백업 AI 및 코드 검증
- **Hugging Face Transformers**: 한국어 NLP 모델
- **LangChain**: AI Agent 오케스트레이션

### 5.2 크롤링 기술
- **Playwright**: 동적 웹사이트 크롤링
- **Beautiful Soup**: HTML 파싱
- **Selenium**: 복잡한 상호작용이 필요한 사이트
- **Scrapy**: 대규모 크롤링 작업

### 5.3 모니터링 및 적응
- **ChangeDetection.io**: 웹 변화 감지
- **Sentry**: 에러 모니터링
- **Prometheus**: 성능 메트릭
- **Redis**: 캐싱 및 세션 관리

## 6. 우선순위 및 일정

### Phase 1: 기본 AI 매크로 생성 (3주)
- [ ] 자연어 처리 엔진 구축
- [ ] 기본 매크로 생성 AI Agent
- [ ] 주요 사이트 (네이버, 다음) 템플릿
- [ ] 생성 위저드 UI

### Phase 2: 동적 적응 시스템 (3주)
- [ ] 사이트 변화 감지 엔진
- [ ] 자동 매크로 업데이트 시스템
- [ ] 성능 모니터링 대시보드
- [ ] 에러 복구 및 재시도 로직

### Phase 3: 고급 기능 및 최적화 (2주)
- [ ] 매크로 성능 최적화
- [ ] 템플릿 라이브러리 확장
- [ ] 사용자 피드백 학습 시스템
- [ ] 배치 처리 및 스케일링

### Phase 4: 통합 및 고도화 (2주)
- [ ] ChangeDetection.io 완전 통합
- [ ] 고급 AI Agent 기능
- [ ] 엔터프라이즈 기능 (권한 관리 등)
- [ ] 성능 최적화 및 문서화

## 7. 성공 지표

### 7.1 기술적 지표
- 자연어 의도 분석 정확도 > 90%
- 매크로 생성 성공률 > 85%
- 사이트 변화 적응 성공률 > 80%
- 평균 매크로 생성 시간 < 2분

### 7.2 사용자 지표
- 사용자 만족도 > 4.3/5.0
- 매크로 재사용률 > 70%
- 사용자 리텐션 > 80%
- 지원 요청 감소 > 60%

## 8. 위험 요소 및 대응방안

### 8.1 기술적 위험
- **AI 모델 한계**: 다중 모델 앙상블 및 인간 검토 시스템
- **사이트 차단**: 다양한 우회 전략 및 프록시 활용
- **성능 저하**: 캐싱 및 최적화 전략

### 8.2 운영적 위험
- **법적 이슈**: 로봇 배제 표준 준수 및 법무 검토
- **비용 증가**: API 사용량 모니터링 및 예산 관리
- **데이터 품질**: 자동 검증 및 품질 관리 시스템