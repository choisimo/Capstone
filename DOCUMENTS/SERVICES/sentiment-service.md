# sentiment-service

## 개요
- 목적: 3클래스(긍/부/중) 및 8감정 분류 점수 산출.

## 인터페이스
- 이벤트(구독): `clean.posts.v1`
- 이벤트(발행): `scores.sentiment.v1`
- 내부 모델 서빙: Ray Serve/TorchServe/Vertex Endpoint

## 데이터/스토리지
- 결과 저장: ClickHouse/ES(쿼리용), Lake(원천/특징)

## 설정(ENV)
- `MODEL_NAME`, `MODEL_VER`
- `BATCH_SIZE`, `MAX_CONCURRENCY`

## 관측성
- Metrics: 처리지연, 정확도(오프라인), 드리프트 지표

## 통신 프로토콜 (Kafka/Pub/Sub)
- Kafka
  - 구독 토픽: `clean.posts.v1` (파티션 키: `dedup_key`)
  - 발행 토픽: `scores.sentiment.v1` (파티션 키: `post_id`)
  - 컨슈머 그룹: `sentiment-service.{env}`
  - 헤더: `trace_id`, `schema_version`, `source`, `channel`, `content_type`, `platform_profile`, `model_ver`
  - 전달 보장: at-least-once, DLQ: `clean.posts.dlq`, `scores.sentiment.dlq`
- Pub/Sub
  - 구독: `clean-posts`
  - 발행: `scores-sentiment`
  - Attributes: 헤더와 동일 매핑
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md`의 `clean.posts.v1`, `scores.sentiment.v1`
- 보안: Kafka(mTLS+ACL), Pub/Sub(IAM)
- 관측성: Lag/스루풋/에러율 모니터, OTel trace 연계

## 백로그
- 온디맨드/배치 혼합 모드, A/B 라우팅
