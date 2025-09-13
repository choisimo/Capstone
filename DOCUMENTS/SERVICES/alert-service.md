# alert-service

## 개요
- 목적: 임계치/변동성 기반 조기경보 산출, Slack/메일/WebSocket 연계.

## 인터페이스
- 이벤트(구독): 집계 지표 스트림 또는 조회 결과
- 이벤트(발행): `ops.alerts.v1`
- 알림 채널: Slack(Webhook), Email, Webhook

## 데이터/스토리지
- 룰/정책 저장, 서프레션 윈도우, 사용자 구독

## 설정(ENV)
- `SLACK_WEBHOOK_URL`(옵션)
- `ALERT_RULES_PATH`

## 관측성
- Metrics: 경보수/유효율, 노이즈율, MTTA

## 통신 프로토콜 (Kafka/Pub/Sub)
- Kafka
  - 구독 토픽(옵션): `scores.sentiment.v1`, `scores.absa.v1`, `analytics.topic.v1` (파티션 키: `post_id`)
  - 발행 토픽: `ops.alerts.v1` (파티션 키: `issue`)
  - 컨슈머 그룹: `alert-service.{env}`
  - 헤더: `trace_id`, `schema_version`, `issue`, `severity`, `rule_id`
  - 전달 보장: at-least-once, DLQ: `ops.alerts.dlq`
- Pub/Sub
  - 구독(옵션): `scores-sentiment`, `scores-absa`, `analytics-topic`
  - 발행: `ops-alerts`
  - Attributes: 헤더와 동일 매핑
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md`의 `scores.*`, `analytics.topic.v1`, `ops.alerts.v1`
- 보안: Kafka(mTLS+ACL), Pub/Sub(IAM)
- 관측성: Lag/스루풋/경보 노이즈율, OTel trace 연계

## 백로그
- 이상탐지(AD) 모델, 사용자별 구독 필터
