# ingest-worker

## 개요
- 목적: `raw.posts.v1` 이벤트를 수신하여 원문 정제/중복제거 후 MongoDB/VectorDB에 저장하고 인덱싱 신호를 발행.
- 담당 범위: 수집→정제→저장 파이프라인의 마이크로 배치/근실시간 처리.
- 운영 프로파일: `PLATFORM_PROFILE=gcp|linux-server`

## 인터페이스
- 이벤트(구독): `raw.posts.v1`
- 이벤트(발행): (
  옵션) `clean.posts.v1` 또는 내부 큐(태깅/집계 트리거)
- REST: 없음
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md`의 `raw.posts.v1`, `clean.posts.v1`

## 처리 로직
- 정제: HTML 제거, 공백/이모지/URL 정규화, 언어감지
- 중복: URL 정규화 해시 + MinHash(옵션), time-window idempotency
- 매핑: 기사 URL→`articles` upsert, 본문→`documents` insert, `vector_id` placeholder
- 인덱싱: VectorDB 임베딩 큐잉, 역색인/키워드 추출(optional)

## 데이터/스토리지
- MongoDB
  - `articles`, `documents` 컬렉션 구조는 `analysis-service` 문서 참조
- VectorDB
  - document 임베딩 저장, `vector_id` ↔ `documents._id`
- 보관/TTL/인덱싱 정책
  - 원시 스냅샷 저장 여부는 수집기 설정에 따름, `documents.ts` 범위 인덱스

## 설정(ENV)
- 필수: `MONGO_URI`, `MONGO_DB`, `KAFKA_BROKERS`
- 컨슈머 그룹: `INGEST_GROUP`(기본 `analysis-ingest`)
- 토픽: `RAW_TOPIC`(기본 `raw.posts.v1`), `SEED_TOPIC`(기본 `seed.news.v1`)
- 발행(옵션): `CLEAN_TOPIC`(기본 `clean.posts.v1`), `SCORES_TOPIC`(기본 `scores.sentiment.v1`)
- 관측(옵션): `INGEST_METRICS_PORT`(Prometheus, 0 또는 미설정 시 비활성)
- 안정성(옵션): `SENTRY_DSN`

참고: 현재 버전은 MongoDB upsert 및 Kafka 발행 중심이며 VectorDB 임베딩은 미구현(추후 추가 예정)입니다.

## 의존성
- 내부 서비스: collector-service/bridge(이벤트 소스)
- 외부 서비스/OSS: Kafka/PubSub, MongoDB, VectorDB, BeautifulSoup/boilerpy3, fasttext/cld3

## 로컬 실행(예시)
- `python BACKEND-ANALYSIS-SERVICE/workers/ingest_worker.py`

## 관측성
- Metrics: `events_in`, `events_deduped`, `docs_written`, `embed_queue`, `latency_ms`, `error_rate`
- Traces: 이벤트→정제→쓰기 단계별 span, `trace_id` 전파
- Logs: 원문 길이/언어/중복여부 요약, 에러 표준 포맷

## 보안
- 인증/인가: 메시지 버스(mTLS/IAM)
- 비밀/키 관리: DB/버스 크리덴셜 비밀관리
- 데이터: PII 필드 제거/가명화 준수

## SLO/성능
- 처리량: ≥ 1K msg/s(스케일아웃 기준)
- 지연: P95 파이프라인 < 3s(배치 크기 100)
- 오류율: < 1%/주, DLQ<0.1%

## 운영/장애 대응
- 재시도/백오프: 네트워크/DB 에러 지수백오프, idempotent upsert
- 리플레이: DLQ 재처리 잡, 시계열 범위 재인게스트 스크립트

## 통신 프로토콜 (Kafka/Pub/Sub)
- Kafka
  - 구독: `raw.posts.v1` (파티션 키: `hash(source + url_norm)`) 컨슈머 그룹 `ingest-worker.{env}`
  - (옵션) 발행: `clean.posts.v1` 파이프라인 분기 시
  - 전달 보장: at-least-once, DLQ: `raw.posts.dlq`, `clean.posts.dlq`
- Pub/Sub
  - 구독: `raw-posts`
  - 발행: `clean-posts`(옵션)
  - Attributes: 헤더 동일 매핑

## 백로그
- 멀티파이프라인 분기(뉴스·커뮤니티·X 등 채널별 규칙)

## 실행 작업 매핑 (Execution Task Mapping)
Ingest 처리 체인 IW1–IW9.

핵심 매핑:
- IW1 컨슈머 설정/파티션 전략: 그룹·파티션 키 일관 (Kafka/PubSub 섹션)
- IW2 정제 파이프라인: HTML/이모지/URL 정규화 + 언어감지
- IW3 중복 제거: URL 정규화 해시 + MinHash/window idempotency
- IW4 문서 매핑/업서트: articles/documents 스키마 반영 + vector_id placeholder
- IW5 이벤트/메시지 발행: `clean.posts.v1` (옵션) + 후속 스코어 큐
- IW6 임베딩 큐잉: VectorDB 비동기 파이프라인 트리거
- IW7 관측성 계측: events_in/deduped/docs_written/latency
- IW8 장애 복구: DLQ 재처리 & 재인게스트 스크립트
- IW9 성능 튜닝: 배치크기/병렬/압축 최적화

교차 의존성:
- Collector(C1–C5), Tagging(T2), NLP(N3–N6), ABSA(A2), Sentiment(S2)
- 공통 X1–X3, X5, X7, X10

추적:
- PR 태그 `[IW2][IW3]`; 초기 기능 컷: IW1–IW5 + IW7
- 튜닝 목표: P95 지연 <3s 달성 후 IW9 최적화 단계 착수
- 미디어 타입 확장(PDF/이미지 OCR)
- 임베딩 비동기 워커 분리 및 캐시
