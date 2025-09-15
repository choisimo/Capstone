**연금 나침반 PRD 캔버스 (Repo 정합 수정본)**

- 문서 버전: 1.1-repo-aligned
- 작성일: 2025-09-15
- 프로젝트 목표: 국민연금 관련 온라인 여론을 수집·정제하고, 감정-페르소나-경험 관계를 시각화 및 RAG 기반 보고서로 제공하는 대화형 분석 에이전트 플랫폼

레포 현황 요약
- 크롤러 코어: BACKEND-WEB-CRAWLER/changedetectionio (Flask) + ChangeDetection API
- 에이전트/게이트웨이: BACKEND-WEB-COLLECTOR/agent_service.py (FastAPI) — 워치 생성·업데이트, UI 헬퍼 API 제공
- 브리지/버스 연동: BACKEND-WEB-COLLECTOR/bridge.py — ChangeDetection 스냅샷을 raw.posts.v1 이벤트로 퍼블리시(Kafka/PubSub/stdout)
- 간이 에이전트 UI: BACKEND-WEB-COLLECTOR/frontend (Vite React)
- 대시보드 앱: FRONTEND-DASHBOARD (Vite React + shadcn/ui + Tailwind) — 샘플 분석 화면 존재(실데이터 미연동)
- 부족한 부분: MongoDB/VectorDB, RAG, Gemini 연동, 메쉬망 API/시각화, 문서/댓글 스키마 계층, 뉴스 중심 분석

가치 제안
- 데이터 기반 투명성: 실시간 여론 수집과 구조화된 감정·경험 맥락 제공
- 정책 인사이트: 집단별 이슈의 원인-감정 연쇄를 RAG 보고서로 전달
- 대화형 탐색: 질문 의도에 따라 검색·요약·분석 경로를 유연하게 안내

핵심 사용자
- 정책/연구: 정책 설계·효과 평가를 위한 정량·정성 분석
- 언론/미디어: 기사 주제별 여론 형성 구조와 인용 가능한 원문 확보
- 일반 시민: 타 집단의 관점과 감정 구조에 대한 이해 증진

기능 범위 (MVP → 확장)
- MVP 수집/전달:
  - 수집: ChangeDetection 워치로 뉴스/커뮤니티 페이지 감시
  - 전달: 최신 스냅샷을 이벤트로 발행(raw.posts.v1)
  - 제어: 자연어→브라우저 스텝 생성(POST /api/v1/agent/generate-steps) 및 워치 생성
- MVP 분석/시각화(프로토):
  - 대시보드: 샘플 차트에 실제 지표 연동(언급량/감정 분포)
  - 필터: 기간·채널·키워드 기초 필터
- V2 분석/지식:
  - 스토리지: MongoDB(articles, documents), VectorDB(임베딩/유사도)
  - 태깅: 감정/페르소나/경험 태깅(Gemini 함수호출형)
  - 메쉬망: 감정-페르소나-경험-키워드 2.5D 그래프
  - RAG: 드래그앤드롭 구성요소 기반 보고서 생성
  - 대화형: 의도 인식→검색/RAG/요약 경로 선택 응답

시스템 아키텍처
- 구조: Client(React) → API Gateway(FastAPI) → Microservices(Crawling/Analysis/RAG) → Databases(MongoDB/VectorDB)
- 현행 구성 맵핑:
  - agent_service.py: 게이트웨이 초석(워치, UI 헬퍼)
  - changedetectionio: 크롤러/변화 감지
  - bridge.py: 이벤트 브리지(버스 전송)
  - 신규 마이크로서비스: analysis-service(Mongo/Vector/RAG/Gemini)

백엔드 API 설계
- 현행(사용 가능):
  - POST /api/v1/agent/generate-steps: 자연어→브라우저 스텝(룰베이스)
  - POST /api/v1/agent/create-watch: 워치 생성(+선택적 재체크)
  - PUT /api/v1/agent/update-watch/{uuid}: 워치 업데이트
  - GET /api/v1/ui/*: CDIO 프락시(정보/검색/스냅샷/태그/수정)
- 신규(분석/RAG 서비스):
  - GET /api/mesh-data: 전체 메쉬망(노드/링크, 집계 기준 포함)
  - GET /api/articles: 뉴스 목록/검색(키워드·기간·출처)
  - GET /api/articles/{article_id}/mesh-data: 기사 중심 메쉬망
  - GET /api/documents: 필터링된 원문 목록(페이지네이션)
  - POST /api/generate-report: 선택 노드 조합→RAG 보고서
  - POST /api/chat: 의도 인식→검색/RAG/요약 대화 응답
- 이벤트 인테그레이션:
  - 스키마: CONTRACTS/api-and-events.md, raw.posts.v1에 정합
  - 브리지 설정: MESSAGE_BUS, RAW_TOPIC, KAFKA_BROKERS/PUBSUB_PROJECT

데이터 모델
- MongoDB
  - articles: title, url, summary, published_at, source, keywords
  - documents: content, source, timestamp, article_id(Ref), metadata(sentiment/persona/experience_tags/keywords), vector_id
- VectorDB
  - 임베딩: ko-sroberta-multitask 또는 text-embedding-004
  - 링크: vector_id ↔ documents._id
- 파이프라인 연결:
  - ChangeDetection 스냅샷 → bridge 이벤트 → ingest-worker(신규) → 정제/중복제거 → Mongo/Vector 저장 → 인덱싱/집계

AI 분석 엔진
- 태깅: Gemini(Function Calling)로 감정/페르소나/경험 원인 분석
- 대화형: 의도 분류(FAQ/설명·요약·비교·세그먼트 여론) → 동적 프롬프트
- RAG: 필터/선택 노드 기반 관련 청크 검색 → 정책적 시사점 포함 보고서 생성

프론트엔드
- 앱 프레임: FRONTEND-DASHBOARD 활용
- 주요 컴포넌트(신규):
  - MeshVisualization: 2.5D 그래프(react-force-graph/three)
  - FilterSidebar: 기간/감정/페르소나/키워드 필터
  - ReportPanel: 노드 드래그앤드롭 → RAG 요청/결과 표시
  - ChatAgent: 대화형 질의/응답 UI
  - NewsAnalysis: 기사 선택 UI + 기사 중심 메쉬망
- 연동 계획:
  - 현 Analytics 더미 데이터 → /api/mesh-data, /api/documents 실연동
  - 라우팅: 전체 여론, 뉴스 분석, 심층 보고서, AI 에이전트 탭 구성

환경 변수/운영
- ChangeDetection: CHANGEDETECTION_BASE_URL, CHANGEDETECTION_API_KEY
- Agent: AGENT_PORT, AGENT_ALLOW_EXECUTE_JS, AGENT_RECHECK_ON_*
- Bridge/Bus: MESSAGE_BUS(stdout|kafka|pubsub), RAW_TOPIC, KAFKA_BROKERS, PUBSUB_PROJECT, INCLUDE_HTML
- 분석 서비스(신규): MONGO_URI, MONGO_DB, VECTOR_DB_URL, GEMINI_API_KEY

마일스톤(16주)
- 1단계(1–4주) 기반/수집
  - ChangeDetection/Agent/Bridge 통합 운영
  - Ingest 워커(정제/중복/언어감지) 및 Mongo/Vector 쓰기
  - /api/articles, /api/documents 베이식 구현
- 2단계(5–8주) 태깅/시각화
  - Gemini 태깅 파이프라인(배치→준실시간)
  - /api/mesh-data 1차(집계 중심) + MeshVisualization 기본
- 3단계(9–12주) 뉴스/RAG/대화
  - 기사 중심 메쉬망(/api/articles/{id}/mesh-data)
  - 드래그앤드롭 RAG(/api/generate-report), ChatAgent MVP
- 4단계(13–16주) 통합/품질
  - 필터 전면 연동, E2E 테스트, 성능/비용 최적화
  - 발표·문서화(아키/운영/보안/사용가이드)

성공 지표
- 수집/저장: 일일 신규 문서 N≥10K, 중복율 ≤5%
- 태깅 품질: 감정/경험 태깅 휴리스틱 검수 F1 ≥0.8
- 검색/응답: Top-k 유사도 적중률@5 ≥0.7, RAG 보고서 만족도 ≥4.2/5
- UX: 그래프 인터랙션 60fps(95% 프레임), 페이지 TTI < 3s

리스크/대응
- 저작권/로봇배제: robots.txt 존중, 링크/요약 중심 사용, 법무 검토
- 개인정보: 해시/가명화, 민감정보 필터링, 보존기간 정책
- API 비용: 임베딩/생성 캐시, 배치 윈도우, 프롬프트 최적화
- 품질 편향: 모델 편향 모니터링, 휴먼 검수 라벨셋 개선

트레이서빌리티(레포 ↔ PRD)
- agent_service.py ↔ 워치 생성/업데이트/검색(UI 헬퍼)
- bridge.py ↔ raw.posts.v1 이벤트 발행(수집→인게스트)
- FRONTEND-DASHBOARD/src/pages/Analytics.tsx ↔ 분석 화면(실데이터 연동 대상)
- DOCUMENTS/CONTRACTS/api-and-events.md ↔ 이벤트 스키마 기준

오픈 이슈
- 기사-댓글 매핑: ChangeDetection 소스 단위 수집과 articles 연계 전략
- 경험 태그 온톨로지: 표준 태그 셋 정의 및 스키마 버전 관리
- 그래프 레이아웃: 대용량 노드 수 안정적 렌더링/집계 전략
- 벤치마크: 태깅·RAG 품질 측정용 골든셋 구성/관리
