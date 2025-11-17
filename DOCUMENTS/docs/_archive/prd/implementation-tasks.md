---
docsync: true
last_synced: 2025-09-30T09:26:00+0900
title: 미구현 기능 작업 배분
version: 1.0
status: active
---
# 미구현 기능 작업 배분 문서

## 문서 정보
- **작성일**: 2025-09-30
- **상태**: Active
- **목적**: 실제 코드 리뷰 기반 미구현 기능 파악 및 작업 배분

---

## 코드 리뷰 요약

### 구현 완료 서비스
1. **Alert Service (8004)** - 95% 완성
   -  알림 규칙 CRUD
   -  알림 발송 (Email, Slack, Webhook)
   -  알림 히스토리 조회
   -  구독 관리
   -  통계 API
   -  테스트 엔드포인트

2. **Analysis Service (8001)** - 80% 완성
   -  감성 분석 (RoBERTa 모델)
   -  배치 처리
   -  히스토리 조회
   -  트렌드 분석 (부분 구현)
   -  리포트 생성 (부분 구현)

3. **OSINT Orchestrator (8005)** - 70% 완성
   -  작업 큐 관리
   -  워커 등록/하트비트
   -  작업 할당
   -  결과 제출
   -  작업 재시도 로직 (기본 구현)
   -  우선순위 큐 최적화
   -  작업 의존성 해결

---

## 미구현 기능 목록

### 1. Analysis Service - 트렌드 분석 완성  HIGH

**현재 상태**: 기본 구조만 존재, 실제 로직 미구현

**구현 필요 사항**:
```python
# /app/services/trend_service.py

class TrendService:
    async def analyze_trends(
        self,
        period: str,  # daily, weekly, monthly
        entity: str,
        start_date: str,
        end_date: str
    ) -> TrendAnalysisResponse:
        """
        TODO: 구현 필요
        - 기간별 감성 집계
        - 볼륨 트렌드 계산
        - 변화율 산출
        - 주요 키워드 추출
        """
        pass
    
    async def get_trending_keywords(
        self,
        period: str,
        limit: int
    ) -> List[KeywordTrend]:
        """
        TODO: 구현 필요
        - TF-IDF 기반 키워드 추출
        - 빈도 증가율 계산
        - 감성 점수 연계
        """
        pass
```

**작업 범위**:
- [ ] 시계열 데이터 집계 로직
- [ ] 트렌드 변화 감지 알고리즘
- [ ] 키워드 추출 (TF-IDF/BERTopic)
- [ ] 캐싱 전략 구현
- [ ] API 엔드포인트 테스트

**예상 공수**: 3일
**담당자**: 데이터AI팀
**우선순위**: HIGH

---

### 2. Analysis Service - 리포트 생성 완성  HIGH

**현재 상태**: 스켈레톤 코드만 존재

**구현 필요 사항**:
```python
# /app/services/report_service.py

class ReportService:
    async def generate_report(
        self,
        request: ReportRequest,
        background_tasks: BackgroundTasks
    ) -> ReportResponse:
        """
        TODO: 구현 필요
        - 감성 분석 리포트 (기간별 요약)
        - 트렌드 분석 리포트 (시각화 포함)
        - 종합 요약 리포트 (LLM 기반)
        - PDF/Excel 출력
        """
        pass
    
    async def download_report(
        self,
        report_id: int,
        format: str
    ) -> FileResponse:
        """
        TODO: 구현 필요
        - JSON → PDF 변환
        - JSON → Excel 변환
        - 차트 이미지 생성
        """
        pass
```

**작업 범위**:
- [ ] 리포트 템플릿 설계
- [ ] 데이터 집계 로직
- [ ] PDF 생성 (ReportLab/WeasyPrint)
- [ ] Excel 생성 (openpyxl)
- [ ] 차트 생성 (matplotlib/plotly)
- [ ] 백그라운드 작업 처리

**예상 공수**: 4일
**담당자**: 데이터AI팀
**우선순위**: HIGH

---

### 3. Collector Service - 고급 검증 로직  MEDIUM

**현재 상태**: 기본 URL 검증만 구현

**구현 필요 사항**:
```python
# /app/services/validation_service.py

class ValidationService:
    async def validate_content_quality(
        self,
        content: Dict[str, Any]
    ) -> QualityScore:
        """
        TODO: 구현 필요
        - 컨텐츠 길이 검증
        - 한국어 비율 검증
        - 광고/스팸 감지
        - 관련성 점수 (키워드 기반)
        """
        pass
    
    async def detect_duplicates(
        self,
        content: Dict[str, Any],
        threshold: float = 0.85
    ) -> bool:
        """
        TODO: 구현 필요
        - URL 해시 중복 체크
        - 컨텐츠 유사도 (TF-IDF)
        - MinHash LSH 구현
        """
        pass
```

**작업 범위**:
- [ ] 품질 점수 산출 로직
- [ ] 중복 감지 알고리즘
- [ ] 스팸 필터 (규칙 기반)
- [ ] Redis 캐싱 연동

**예상 공수**: 3일
**담당자**: 데이터수집팀
**우선순위**: MEDIUM

---

### 4. ABSA Service - 배치 페르소나 재계산  MEDIUM

**현재 상태**: 단건 재계산만 구현

**구현 필요 사항**:
```python
# /app/services/persona_scheduler.py

class PersonaScheduler:
    async def schedule_batch_recalculation(
        self,
        criteria: Dict[str, Any]
    ) -> BatchJobResponse:
        """
        TODO: 구현 필요
        - Stale 페르소나 자동 감지
        - 우선순위 기반 스케줄링
        - 배치 작업 큐 관리
        - 진행 상황 추적
        """
        pass
    
    async def recalculate_all_stale(
        self,
        batch_size: int = 50
    ) -> BatchJobResponse:
        """
        TODO: 구현 필요
        - 24시간 이상 stale 페르소나 조회
        - 배치 재계산 실행
        - 에러 핸들링 및 재시도
        """
        pass
```

**작업 범위**:
- [ ] Celery/RQ 작업 큐 연동
- [ ] 스케줄러 구현 (APScheduler)
- [ ] 진행 상황 API
- [ ] 에러 복구 로직

**예상 공수**: 3일
**담당자**: 데이터AI팀
**우선순위**: MEDIUM

---

### 5. OSINT Services - Planning Service 구현  MEDIUM

**현재 상태**: 기본 구조만 존재, 로직 없음

**구현 필요 사항**:
```python
# BACKEND-OSINT-PLANNING-SERVICE/app/services/planning_service.py

class PlanningService:
    async def create_collection_plan(
        self,
        plan_request: PlanRequest
    ) -> Plan:
        """
        TODO: 구현 필요
        - 소스 우선순위 결정
        - 수집 일정 최적화
        - 리소스 할당 계산
        - 의존성 그래프 생성
        """
        pass
    
    async def execute_plan(
        self,
        plan_id: int
    ) -> ExecutionResponse:
        """
        TODO: 구현 필요
        - 계획을 Orchestrator 작업으로 변환
        - 작업 등록 및 모니터링
        - 실행 상태 추적
        """
        pass
```

**작업 범위**:
- [ ] 계획 알고리즘 설계
- [ ] Orchestrator 연동
- [ ] 계획 템플릿 시스템
- [ ] 실행 모니터링 대시보드

**예상 공수**: 4일
**담당자**: OSINT팀
**우선순위**: MEDIUM

---

### 6. OSINT Services - Source Service 크롤러 통합  MEDIUM

**현재 상태**: Mock 감지만 구현, 실제 크롤러 통합 없음

**구현 필요 사항**:
```python
# BACKEND-OSINT-SOURCE-SERVICE/app/services/integrated_crawler_manager.py

class IntegratedCrawlerManager:
    async def execute_crawl(
        self,
        source_id: int,
        crawler_type: str
    ) -> CrawlResult:
        """
        TODO: 완성 필요
        - 직접 구현 크롤러 호출
        - changedetection.io API 연동
        - ScrapeGraphAI 통합
        - 결과 집계 및 검증
        """
        # 현재: Mock 데이터 감지만 구현
        # 필요: 실제 크롤링 로직
        pass
    
    async def aggregate_results(
        self,
        crawl_results: List[CrawlResult]
    ) -> AggregatedResult:
        """
        TODO: 구현 필요
        - 중복 제거
        - 품질 점수 통합
        - 소스별 가중치 적용
        """
        pass
```

**작업 범위**:
- [ ] 직접 크롤러 연동 (BACKEND-WEB-COLLECTOR)
- [ ] changedetection.io API 클라이언트
- [ ] ScrapeGraphAI 어댑터 구현
- [ ] 결과 집계 로직

**예상 공수**: 5일
**담당자**: OSINT팀 + 데이터수집팀
**우선순위**: MEDIUM

---

### 7. API Gateway - 인증/인가 구현  LOW

**현재 상태**: CORS만 구현, JWT 인증 없음

**구현 필요 사항**:
```python
# /app/middleware/auth.py

class JWTMiddleware:
    async def __call__(
        self,
        request: Request,
        call_next
    ):
        """
        TODO: 구현 필요
        - JWT 토큰 검증
        - RBAC 역할 확인
        - 권한별 엔드포인트 접근 제어
        """
        pass

# /app/middleware/rate_limit.py

class RateLimitMiddleware:
    async def __call__(
        self,
        request: Request,
        call_next
    ):
        """
        TODO: 구현 필요
        - IP별 요청 제한
        - 사용자별 요청 제한
        - Redis 기반 카운팅
        - 429 응답 처리
        """
        pass
```

**작업 범위**:
- [ ] JWT 인증 미들웨어
- [ ] RBAC 정책 엔진
- [ ] Rate Limiting (Redis)
- [ ] API Key 관리

**예상 공수**: 3일
**담당자**: Platform팀
**우선순위**: LOW (현재 내부망 운영)

---

### 8. Frontend - 실시간 대시보드 완성  HIGH

**현재 상태**: 샘플 화면만 존재, 실제 데이터 미연동

**구현 필요 사항**:
```tsx
// /src/components/RealTimeDashboard.tsx

export function RealTimeDashboard() {
  /**
   * TODO: 구현 필요
   * - Analysis Service API 연동
   * - WebSocket 실시간 업데이트
   * - 차트 라이브러리 통합 (recharts)
   * - 필터링 및 드릴다운
   */
  return <div>샘플 화면</div>
}

// /src/lib/api.ts

export const api = {
  /**
   * TODO: 구현 필요
   * - API Gateway 클라이언트
   * - 에러 핸들링
   * - 재시도 로직
   * - 캐싱 전략
   */
}
```

**작업 범위**:
- [ ] API 클라이언트 구현
- [ ] 실시간 차트 컴포넌트
- [ ] 페르소나 네트워크 시각화 완성
- [ ] 알림 센터 UI

**예상 공수**: 5일
**담당자**: Frontend팀
**우선순위**: HIGH

---

## 작업 우선순위 매트릭스

| 작업 | 우선순위 | 공수 | 의존성 | 담당팀 |
|------|---------|------|--------|--------|
| Analysis - 트렌드 분석 |  HIGH | 3일 | 없음 | 데이터AI |
| Analysis - 리포트 생성 |  HIGH | 4일 | 트렌드 분석 | 데이터AI |
| Frontend - 대시보드 |  HIGH | 5일 | Analysis API | Frontend |
| Collector - 품질 검증 |  MEDIUM | 3일 | 없음 | 데이터수집 |
| ABSA - 배치 재계산 |  MEDIUM | 3일 | 없음 | 데이터AI |
| OSINT - Planning |  MEDIUM | 4일 | Orchestrator | OSINT |
| OSINT - 크롤러 통합 |  MEDIUM | 5일 | Planning | OSINT+수집 |
| Gateway - 인증/인가 |  LOW | 3일 | 없음 | Platform |

---

## Sprint 계획

### Sprint 1 (Week 1-2) - 핵심 분석 기능  75% 완료
**목표**: 트렌드 분석 및 리포트 생성 완성

- [x] **Task 1.1**: Analysis Service - 트렌드 분석 구현
  - 담당: 데이터AI팀
  - 기간: 3일
  - 산출물:  완성된 trend_service.py, 한국어 키워드 추출 (KoNLPy)
  - 완료일: 2025-09-30

- [x] **Task 1.2**: Analysis Service - 리포트 생성 구현
  - 담당: 데이터AI팀
  - 기간: 4일
  - 산출물:  report_service.py 완성, PDF/Excel 출력 구현
  - 완료일: 2025-09-30

- [x] **Task 1.3**: Frontend - API 클라이언트 구현
  - 담당: Frontend팀
  - 기간: 2일
  - 산출물:  src/lib/api.ts, 에러 핸들링, 재시도, 캐싱
  - 완료일: 2025-09-30

### Sprint 2 (Week 3-4) - 데이터 품질 및 UI
**목표**: 수집 품질 향상 및 대시보드 완성

- [ ] **Task 2.1**: Collector - 품질 검증 로직
  - 담당: 데이터수집팀
  - 기간: 3일
  - 산출물: validation_service.py

- [ ] **Task 2.2**: Frontend - 대시보드 완성
  - 담당: Frontend팀
  - 기간: 3일
  - 산출물: 실시간 차트, 필터링

- [ ] **Task 2.3**: ABSA - 배치 재계산
  - 담당: 데이터AI팀
  - 기간: 3일
  - 산출물: persona_scheduler.py, Celery 연동

### Sprint 3 (Week 5-6) - OSINT 완성
**목표**: OSINT 서비스 통합 완료

- [ ] **Task 3.1**: OSINT Planning Service
  - 담당: OSINT팀
  - 기간: 4일
  - 산출물: planning_service.py, 계획 알고리즘

- [ ] **Task 3.2**: OSINT Source - 크롤러 통합
  - 담당: OSINT팀 + 데이터수집팀
  - 기간: 5일
  - 산출물: 통합 크롤러 매니저

### Sprint 4 (Week 7+) - 보안 및 최적화
**목표**: 프로덕션 준비

- [ ] **Task 4.1**: API Gateway - 인증/인가
  - 담당: Platform팀
  - 기간: 3일
  - 산출물: JWT 미들웨어, RBAC

- [ ] **Task 4.2**: 성능 최적화
  - 담당: 전체팀
  - 기간: 지속적
  - 산출물: 캐싱, 인덱싱, 쿼리 최적화

---

## 작업 추적

### 진행 상황 체크리스트

#### Analysis Service
- [x] 트렌드 분석 완성  (2025-09-30)
- [x] 리포트 생성 완성  (2025-09-30)
  - [x] 실제 데이터 기반 감성 리포트
  - [x] 실제 데이터 기반 트렌드 리포트
  - [x] 종합 요약 리포트
  - [x] PDF 출력 (ReportLab)
  - [x] Excel 출력 (openpyxl)
- [x] 한국어 키워드 추출 (KoNLPy)  (2025-09-30)
- [ ] 단위 테스트 (≥80% 커버리지)
- [ ] API 문서 업데이트

#### Collector Service
- [ ] 품질 검증 로직
- [ ] 중복 감지 구현
- [ ] 성능 테스트 (100 pages/min)

#### ABSA Service
- [ ] 배치 재계산 스케줄러
- [ ] Celery 작업 큐
- [ ] 모니터링 대시보드

#### OSINT Services
- [ ] Planning Service 구현
- [ ] Source Service 크롤러 통합
- [ ] Orchestrator 최적화

#### Frontend
- [x] API 클라이언트 완성  (2025-09-30)
  - [x] 타임아웃 처리
  - [x] 재시도 로직 (Exponential backoff)
  - [x] 캐싱 전략 (5분 TTL)
  - [x] 리포트 생성/다운로드 API
  - [x] 페르소나 분석 API
  - [x] 감성 통계 API
- [x] 실시간 대시보드  (2025-09-30)
  - [x] API 통합 완료
  - [x] 차트 컴포넌트 구현 (recharts)
  - [x] 필터링 UI (날짜 범위)
  - [x] 자동 리프레시 (30초)
- [x] 페르소나 네트워크 시각화  (기존 완료)
- [ ] 알림 센터 (Optional)

#### OSINT Services
- [x] Planning Service 구현  (2025-09-30)
- [ ] Source Service 크롤러 통합 (향후)
- [ ] Orchestrator 최적화 (향후)

#### API Gateway
- [x] JWT 인증  (2025-09-30)
- [x] RBAC 구현  (2025-09-30)
- [x] Rate Limiting  (2025-09-30)

---

## 관련 문서
- [ABSA Service PRD](absa-service-detailed-prd.md)
- [Analysis Service PRD](analysis-service-detailed-prd.md)
- [Collector Service PRD](collector-service-detailed-prd.md)
- [Alert Service PRD](alert-service-detailed-prd.md)
- [OSINT Services PRD](osint-services-detailed-prd.md)

---

**최종 업데이트**: 2025-09-30
**다음 리뷰**: 매주 월요일
**책임자**: Platform Team Lead
