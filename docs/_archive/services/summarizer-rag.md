# summarizer-rag

## 개요
- 목적: 문서 임베딩+벡터 검색 기반 근거 중심 요약/논거 제공(온디맨드 API).

## 인터페이스
- REST: `POST /v1/summarize` (api-gateway 경유)
- 데이터 접근: VectorDB(pgvector/Milvus), 원문 링크/스니펫 반환

## 데이터/스토리지
- 임베딩 테이블: `posts_embeddings`(pgvector: id, embedding, meta)

## 설정(ENV)
- `EMBED_MODEL`, `LLM_PROVIDER`, `LLM_MODEL`
- `VECTOR_DB_URL`

## 관측성
- Metrics: 응답지연, 토큰/비용, 캐시히트율

## 통신 프로토콜 (Kafka/Pub/Sub)
- 주 통신: REST 온디맨드(`POST /v1/summarize`), Kafka 사용 없음
- 데이터 접근: VectorDB/검색 인덱스 직접 조회(read-only)
- 헤더 전달: `trace_id`를 API-Gateway로부터 전파하여 분산추적 유지

## 백로그
- 요약 템플릿 버전관리, reranking 도입, 비용 캐핑

## 실행 작업 매핑 (Execution Task Mapping)
요약·RAG 파이프라인 R1–R10.

핵심 매핑:
- R1 문서 임베딩 스키마: posts_embeddings 구조/메타 확정
- R2 임베딩 생성 워커: 배치/실시간 전략(ingest 후속)
- R3 벡터 검색 래퍼: pgvector/Milvus 플러그 인터페이스
- R4 후보 집합 필터: 언어/길이/중복/시간 윈도우 필터
- R5 컨텍스트 압축: 토큰 한도 내 세그먼트 선택
- R6 LLM 요약 체인: Prompt 템플릿/시스템 규칙/토큰 한도
- R7 비용 & 쿼터 모니터: 토큰/초당/일일 비용 추적
- R8 캐시/중복 억제: 동일 질의+컨텍스트 결과 캐시
- R9 품질 평가 루프: 요약 길이/커버리지/출처 인용 비율
- R10 실패 폴백: LLM 실패 시 통계/규칙 요약 대체

교차 의존성:
- Ingest(IW6), Tagging(T2), Analysis(AN5), Gateway(G5), Event-Analysis(EA5)
- 공통 X1–X3, X5, X7, X10

추적:
- PR 태그 `[R6][R8]`; 초기 기능 컷: R1–R6 + R8 + R10
- 품질 루프(R9) 활성 조건: 평균 사용자 만족도 메트릭 수집 후
