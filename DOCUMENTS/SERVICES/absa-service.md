# absa-service

## 개요
- 목적: Aspect 기반 감성(ABSA) 산출 및 근거(evidence span) 추출.

## 인터페이스
- 이벤트(구독): `clean.posts.v1`
- 이벤트(발행): `scores.absa.v1`
- 스키마: `aspect`, `polarity`, `evidence_span`, `model_ver`

## 데이터/스토리지
- 근거 인덱스: ES/VectorDB(옵션)

## 설정(ENV)
- `ASPECT_SET`(정의된 정책 속성 셋)
- `MODEL_NAME`, `MODEL_VER`

## 관측성
- Metrics: 근거 커버리지, 처리지연

## 통신 프로토콜 (Kafka/Pub/Sub)
- Kafka
  - 구독 토픽: `clean.posts.v1` (파티션 키: `dedup_key`)
  - 발행 토픽: `scores.absa.v1` (파티션 키: `post_id`)
  - 컨슈머 그룹: `absa-service.{env}`
  - 헤더: `trace_id`, `schema_version`, `source`, `channel`, `content_type`, `platform_profile`, `model_ver`
  - 전달 보장: at-least-once, DLQ: `clean.posts.dlq`, `scores.absa.dlq`
- Pub/Sub
  - 구독: `clean-posts`
  - 발행: `scores-absa`
  - Attributes: 헤더와 동일 매핑
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md`의 `clean.posts.v1`, `scores.absa.v1`
- 보안: Kafka(mTLS+ACL), Pub/Sub(IAM)
- 관측성: Lag/스루풋/에러율 모니터, OTel trace 연계

## 백로그
- 추출식/분류식 혼합, 라벨링 툴 연계
