# topic-modeler

## 개요
- 목적: 토픽 추출(LDA/BERTopic)과 시계열 추이 산출.

## 인터페이스
- 이벤트(구독): `clean.posts.v1`
- 이벤트(발행): `analytics.topic.v1`

## 데이터/스토리지
- 토픽 용어·가중치 저장, 시계열 머티리얼라이즈드 뷰(ClickHouse)

## 설정(ENV)
- `TOPIC_MODEL=lda|bertopic`
- `EMBEDDING_MODEL`

## 관측성
- Metrics: 토픽 수, 코히런스, 처리지연

## 통신 프로토콜 (Kafka/Pub/Sub)
- Kafka
  - 구독 토픽: `clean.posts.v1` (파티션 키: `dedup_key`)
  - 발행 토픽: `analytics.topic.v1` (파티션 키: `post_id`)
  - 컨슈머 그룹: `topic-modeler.{env}`
  - 헤더: `trace_id`, `schema_version`, `source`, `channel`, `content_type`, `platform_profile`, (선택) `model_ver`
  - 전달 보장: at-least-once, DLQ: `clean.posts.dlq`, `analytics.topic.dlq`
- Pub/Sub
  - 구독: `clean-posts`
  - 발행: `analytics-topic`
  - Attributes: 헤더와 동일 매핑
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md`의 `clean.posts.v1`, `analytics.topic.v1`
- 보안: Kafka(mTLS+ACL), Pub/Sub(IAM)
- 관측성: Lag/스루풋/에러율 모니터, OTel trace 연계

## 백로그
- 동적 토픽 병합/분할, 최신성 가중치
