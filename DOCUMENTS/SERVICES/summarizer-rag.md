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
