# collector-service

## 개요
- 목적: 온라인 채널 수집. changedetection.io(웹 변경 감지)·커스텀 커넥터를 통해 `raw.posts.v1` 이벤트로 게시.
- 담당 범위: 크롤링 스케줄·로그인/탐색 스텝 관리, 중복 기초 필터링(헤더), 실패 재시도.

## 인터페이스
- REST(관리): 커넥터 등록/상태, changedetection 연계(Watch 동기화)
- 이벤트(발행): `raw.posts.v1`
- 이벤트(구독): (옵션) 수집 설정 변경 이벤트
- 외부 OSS API: `BACKEND-WEB-CRAWLER/docs/api-spec.yaml` (changedetection.io)

## 데이터/스토리지
- 상태: 수집 메타, 마지막 오프셋/해시
- 임시: 원시 HTML/스크린샷(옵션, GCS/MinIO)

## 설정(ENV)
- `CHANGEDETECTION_BASE_URL`, `CHANGEDETECTION_API_KEY`
- `KAFKA_BROKERS` or `PUBSUB_PROJECT`
- `RAW_TOPIC=raw.posts.v1`

## 의존성
- 외부: changedetection.io, Kafka/Redpanda 또는 Pub/Sub

## 로컬 실행
- changedetection: `BACKEND-WEB-CRAWLER/docker-compose.yml`
- 브릿지 워커: `python -m collector.bridge`

## 관측성
- Metrics: 수집율, 실패율, 재시도 횟수, 지연
- Logs: 사이트별 결과/오류, 스텝 스크린샷 경로

## 보안
- 사이트 정책 준수, 속도 제한, 크리덴셜 보관(Secrets)

## 통신 프로토콜 (Kafka/Pub/Sub)
- Kafka
  - 발행 토픽: `raw.posts.v1` (파티션 키: `hash(source + url_norm)`)
  - 컨슈머 그룹: `collector-service.{env}` (제어/설정 이벤트 사용 시)
  - 헤더: `trace_id`, `schema_version`, `source`, `channel`, `content_type`, `platform_profile`
  - 전달 보장: at-least-once, 지수 백오프 재시도, DLQ: `raw.posts.dlq`
- Pub/Sub
  - 토픽: `raw-posts`
  - Attributes: 헤더와 동일 매핑
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md`의 `raw.posts.v1`
- 보안: Kafka(mTLS+ACL), Pub/Sub(IAM)
- 관측성: Lag/스루풋/에러율 모니터, OTel trace 연계

## 백로그
- `DOCUMENTS/TODO/CRAWLER/ai-agent-function-prd.txt`의 AI 스텝 생성 API 연계
