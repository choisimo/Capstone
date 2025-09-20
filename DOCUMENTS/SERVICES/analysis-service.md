# analysis-service

## 개요
- 목적: 메쉬 네트워크 기반 노드-링크 분석과 뉴스/원문 검색·보고서·대화형 분석 API를 단일 서비스로 제공.
- 담당 범위: `mesh-data`, `articles`, `documents`, `generate-report`, `chat` REST API 및 RAG 조합 로직, 캐시 관리.
- 운영 프로파일: `PLATFORM_PROFILE=gcp|linux-server`

## 인터페이스
- 기본 경로: `/api/v1` (구 `/api/*`는 호환용으로 일시 유지 — deprecated)
- REST
  - `GET /api/v1/mesh-data`
    - query: `from`, `to`, `source[]`, `channel[]`, `lang[]`, `keywords[]`, `persona[]`, `emotion[]`, `experience[]`, `agg=hour|day|week`, `min_weight`, `max_nodes`, `scope=global|article`, `article_id?`
    - resp: `{ nodes: [{id, type, label, weight}], links: [{source, target, weight, pmi}], meta: {window, filters, computed_at} }`
  - `GET /api/v1/articles`
    - query: `q`, `source[]`, `from`, `to`, `page=1`, `size=20`, `sort=recency|popularity`
    - resp: `{ total, items: [{id, title, url, published_at, source, keywords[]}], agg: {by_source:[], by_time:[]} }`
  - `GET /api/v1/articles/{id}/mesh-data`
    - query: `min_weight`, `max_nodes`
    - resp: 기사 스코프 메쉬 노드/엣지
  - `GET /api/v1/documents`
    - query: `q`, `article_id`, `from`, `to`, `lang[]`, `persona[]`, `emotion[]`, `experience[]`, `keywords[]`, `page`, `size`, `sort=recency|relevance`
    - resp: `{ total, items: [{id, ts, source, channel, article_id, text, meta:{sentiment, persona[], experience[], keywords[], lang}, vector_id}], agg: {by_source:[], by_time:[]} }`
  - `POST /api/v1/generate-report`
    - body: `{ nodes: [{type, id|label}], template?: id, options?: {style, length, audience} }`
    - resp: `{ report_id, markdown, citations: [{doc_id, span}], meta }`
  - `POST /api/v1/chat`
    - body: `{ message, context?: {nodes?, filters?, k?} }`
    - resp: RAG/요약/검색 경로 선택 응답 `{ reply, sources:[], route }`
- WebSocket/SSE (옵션)
  - `GET /ws/mesh` 캐시 리프레시/진행률 알림
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md` 기준 + 본 문서의 응답 스키마

## 데이터/스토리지
- 주 저장소(컬렉션)
  - MongoDB
    - `articles`: `{_id, title, url, summary?, published_at, source, keywords[], crawl_hash}`
    - `documents`: `{_id, article_id?, source, channel, ts, text, meta:{sentiment, persona[], experience[], keywords[], lang}, vector_id}`
    - `mesh_cache`: `{_id, scope:{type:global|article, article_id?}, window:{from,to,agg}, filters_hash, nodes[], links[], computed_at, expires_at}`
  - VectorDB(pgvector/Milvus): document 임베딩; `vector_id` ↔ `documents._id`
- 보관/TTL/인덱싱 정책
  - `mesh_cache.expires_at` TTL(기본 6h), `documents.ts` 범위 인덱스, `articles.published_at` 인덱스, `documents.meta.*` 복합 인덱스

## 설정(ENV)
- 필수: `MONGO_URI`, `MONGO_DB`, `VECTOR_DB_URL`
- 선택: `GEMINI_API_KEY`(RAG/생성), `MESH_CACHE_TTL_SEC`(기본 21600), `MAX_MESH_NODES`(기본 500), `MAX_MESH_LINKS`(기본 5000), `AGG_MIN_SUPPORT`(기본 3), `RAG_MAX_TOKENS`

## 의존성
- 내부 서비스: ingest-worker(문서 적재), tagging-service(태깅 메타), mesh-aggregator(캐시/집계)
- 외부 서비스/OSS: MongoDB, pgvector/Milvus, FastAPI, Pydantic, OpenTelemetry, LLM(Gemini)

## 로컬 실행(예시)
- Uvicorn: `uvicorn app.main:app --reload --port 8010`
- 개발 스텁: `BACKEND-ANALYSIS-SERVICE/README.md` 참고

## 관측성
- Metrics: `mesh_cache_hit`, `mesh_build_latency_ms`, `rag_latency_ms`, `db_qps`, `p95_latency_ms`, `error_rate`
- Traces: 요청→쿼리→RAG 체인, 필터/집계 파이프라인 span
- Logs: 표준화 `{ code, message, trace_id }`, 캐시 키/윈도우/노드수 로그

## 보안
- 인증/인가: OAuth2/OIDC(게이트웨이 연동), 서비스간 mTLS(옵션)
- 비밀/키 관리: `GEMINI_API_KEY`, DB 크리덴셜 Secret Manager/Vault
- 데이터: PII 미저장 원칙, 필요 시 가명화 필드만 노출

## SLO/성능
- 지연/처리량/오류율 목표
  - `GET /api/v1/mesh-data`(캐시 적중) P95 < 600ms, 미적중 < 1.5s(50k 노드 이하)
  - `POST /api/v1/generate-report` P95 < 5s(RAG 토큰 한도 내)
  - 오류율 < 0.5%/주

## 운영/장애 대응
- 알람 규칙/대시보드: p95/p99, 에러율, 캐시 미스율, RAG 실패율
- 재시도/리플레이/백오프: 캐시 빌드 실패 시 지수백오프, 이전 스냅샷 서빙
- Degrade 전략: 노드/엣지 상한 축소, 필터 단순화, 샘플링 서빙

## 통신 프로토콜 (Kafka/Pub/Sub)
- 주 통신: REST. 메시지 버스 직접 사용 없음(메쉬 캐시는 DB 트리거/잡으로 갱신)
- 헤더 전파: 게이트웨이 `trace_id`를 수신하여 로그/트레이스에 연계

## 백로그
- GraphQL/Graph streaming(SSE) 지원 검토
- 보고서 템플릿/워크플로우 편집기, 다중 페르소나 비교 뷰
- PMI/NGMI 등 엣지 가중치 선택, 클러스터링 결과 캐시

## 실행 작업 매핑 (Execution Task Mapping)
Analysis 관련 작업 AN1–AN9 및 연계.

핵심 매핑:
- AN1 Query DSL 정의: 필터/집계 표현 기반 (articles/documents)
- AN2 집계 연산자: count/avg/distinct 구현 + 확장 포인트
- AN3 타임 윈도우 함수: hour/day/week bucket + gap fill 로직
- AN4 캐시 계층: mesh_cache & hot query 결과 TTL 관리
- AN5 AuthZ 필터 통합: 사용자/org 역할 기반 필터 삽입
- AN6 쿼리 플래너 비용 메트릭: 실행 플랜 시간/rows 추적
- AN7 머티리얼라이즈드 뷰: 빈번 heavy 패턴 사전 계산
- AN8 멀티테넌트 쿼터: org별 rate / resource limits
- AN9 쿼리 트레이싱/샘플링: 오버헤드 제한된 세부 span 기록

교차 의존성: Mesh-aggregator(M1–M3), NLP 임베딩(N6–N7), Gateway(G1–G5)

추적: PR 태그 `[AN2][AN4]`, 캐시 히트율 ≥ 목표 후 확장(AN7)
