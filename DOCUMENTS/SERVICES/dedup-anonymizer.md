# dedup-anonymizer

## 개요
- 목적: 중복 제거, 스팸/봇 필터, PII 비식별화. `raw.posts.v1` → `clean.posts.v1`.

## 인터페이스
- 이벤트(구독): `raw.posts.v1`
- 이벤트(발행): `clean.posts.v1`
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md`

## 처리 로직
- 중복: URL+해시/MinHash, 윈도우링(시간)
- 스팸/봇: 휴리스틱+ML(옵션)
- 비식별: NER+규칙, `author_hash`만 유지

## 데이터/스토리지
- 룰/사전: 키워드/정규식/블랙리스트
- 감사로그: 비식별 변환 결과(샘플)

## 설정(ENV)
- `WAREHOUSE=clickhouse|bigquery`
- `CLEAN_TOPIC=clean.posts.v1`

## 관측성
- Metrics: 제거율, 비식별 검출율, 처리지연

## 보안
- PII 저장 금지, 샘플링 검증 시 마스킹

## 통신 프로토콜 (Kafka/Pub/Sub)
- Kafka
  - 구독 토픽: `raw.posts.v1` (파티션 키: `hash(source + url_norm)`)
  - 발행 토픽: `clean.posts.v1` (파티션 키: `dedup_key`)
  - 컨슈머 그룹: `dedup-anonymizer.{env}`
  - 헤더: `trace_id`, `schema_version`, `source`, `channel`, `content_type`, `platform_profile`
  - 전달 보장: at-least-once, DLQ: `raw.posts.dlq`, `clean.posts.dlq`
- Pub/Sub
  - 구독: `raw-posts`
  - 발행: `clean-posts`
  - Attributes: 헤더와 동일 매핑
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md` 참조
- 보안: Kafka(mTLS+ACL), Pub/Sub(IAM)
- 관측성: Lag/스루풋/에러율 모니터, OTel trace 연계

## 백로그
- DLP API(GCP) 통합 옵션
