# collector-service

## 개요
- 목적: 온라인 채널 수집. changedetection.io(웹 변경 감지)·커스텀 커넥터를 통해 `raw.posts.v1` 이벤트로 게시.
- 담당 범위: 크롤링 스케줄·로그인/탐색 스텝 관리, 중복 기초 필터링(헤더), 실패 재시도.

## 인터페이스
- REST(관리): 커넥터 등록/상태, changedetection 연계(Watch 동기화)
- 이벤트(발행): `raw.posts.v1`, `summary.events.v1` (요약 기능 활성 시)
- 이벤트(구독): (옵션) 수집 설정 변경 이벤트
- 외부 OSS API: `BACKEND-WEB-CRAWLER/docs/api-spec.yaml` (changedetection.io)

## 데이터/스토리지
- 상태: 수집 메타, 마지막 오프셋/해시
- 임시: 원시 HTML/스크린샷(옵션, GCS/MinIO)

## 설정(ENV)
- `CHANGEDETECTION_BASE_URL`, `CHANGEDETECTION_API_KEY`
- `KAFKA_BROKERS` or `PUBSUB_PROJECT`
- `RAW_TOPIC=raw.posts.v1`
- 요약 기능:
  - `SUMMARY_ENABLED=0|1` (기본 1)
  - `SUMMARY_LLM_ENABLED=0|1` (기본 0, 1이면 LLMClient 사용 placeholder)
  - `SUMMARY_MAX_CHARS` (기본 400)
  - `SUMMARY_KEYPOINTS_MAX` (기본 5)
  - `SUMMARY_TOPIC` (이벤트 토픽 override 및 키워드 fallback. Kafka 기본 `summary.events.v1`, Pub/Sub 기본 `summary-events`)

### Perplexity AI (선택)
- `PPLX_API_KEY` (필수: Perplexity 사용 시)
- `PPLX_BASE_URL` (기본: `https://api.perplexity.ai`)
- `PPLX_MODEL` (기본: `pplx-70b-online`)
- `PPLX_TIMEOUT_SEC` (기본: `30`)

## 의존성
- 외부: changedetection.io, Kafka/Redpanda 또는 Pub/Sub

## 빠른 시작
- 의존성 설치: `pip install requests` (Kafka 사용 시 `confluent-kafka` 또는 `kafka-python` 중 하나, Pub/Sub 사용 시 `google-cloud-pubsub`)
- 환경변수 설정:
  - 필수: `CHANGEDETECTION_BASE_URL`, `CHANGEDETECTION_API_KEY`
  - 버스 선택: `MESSAGE_BUS=stdout|kafka|pubsub`
    - Kafka: `KAFKA_BROKERS=localhost:19092`, `RAW_TOPIC=raw.posts.v1`(기본)
    - Pub/Sub: `PUBSUB_PROJECT=my-gcp-project`, `RAW_TOPIC=raw-posts`(기본)
  - 옵션: `POLL_INTERVAL_SEC=60`, `INCLUDE_HTML=0|1`, `WATCH_TAG=태그명`, `SOURCE=web`, `CHANNEL=changedetection`, `PLATFORM_PROFILE=public-web`
  - Perplexity 사용 시: `PPLX_API_KEY=...`(필수), `PPLX_MODEL`(옵션)
  - 요약 사용 예: `SUMMARY_ENABLED=1 SUMMARY_LLM_ENABLED=0 METRICS_PORT=8009`
- 상태 저장: `.collector_state.json`(기본, 위치 변경은 `COLLECTOR_STATE_PATH`)

## 로컬 실행
- changedetection: `BACKEND-WEB-CRAWLER/docker-compose.yml`
- 브릿지 워커: `python -m collector.bridge`
- 뉴스 워처(요약 stdout 검증):
  ```bash
  MESSAGE_BUS=stdout SUMMARY_ENABLED=1 python BACKEND-WEB-COLLECTOR/news_watcher.py | grep summary.events.v1
  ```
- Prometheus 메트릭 확인:
  ```bash
  MESSAGE_BUS=stdout SUMMARY_ENABLED=1 METRICS_PORT=8009 \
    python BACKEND-WEB-COLLECTOR/news_watcher.py &
  sleep 5
  curl -s localhost:8009/metrics | grep newswatcher_summaries_total
  ```

## 관측성
- Metrics: 수집율, 실패율, 재시도 횟수, 지연
  - 요약 관련: `newswatcher_summaries_total{topic=...}` (발행 카운트), `newswatcher_summary_latency_seconds` (빌드+발행 시간)
- Logs: 사이트별 결과/오류, 스텝 스크린샷 경로

## 요약(summary) 이벤트 흐름
- 트리거: `raw.posts.v1` 발행 직후 특정 채널에 대해 자동 (`SUMMARY_ENABLED=1`)
  - 포함: 기사 본문(`source=news, channel=article`), Perplexity 웹 검색(`source=web, channel=search`), YouTube 비디오(`source=youtube, channel=video`)
  - 제외: 댓글(`channel=comment`)은 노이즈/짧은 텍스트로 기본 비활성 (후속 정책 결정 가능)
- 파이프라인: LLM 사용 플래그(`SUMMARY_LLM_ENABLED=1`) 없으면 휴리스틱 요약 + 정규표현식 기반 facts 추출(amounts/ratios/dates/orgs)
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md` 내 `summary.events.v1` 참고 (필드: id, raw_id, summary, key_points, facts.*, meta.*)
- 헤더: `schema_version=summary.events.v1`, `raw_id` 포함하여 원본과 조인 가능
- 파티션 키(카프카): `hash("summary:" + raw_id)` → raw 이벤트당 1 요약 보장 (idempotent 소비자 구현 용이)
- 토픽명: Kafka 기본 `summary.events.v1`, Pub/Sub 기본 `summary-events` (둘 다 `SUMMARY_TOPIC` 환경변수로 override 가능)
- 크기 제한: 본문 입력 길이 제한 없음(기사 본문은 내부 12k chars truncate), 출력은 `SUMMARY_MAX_CHARS`로 자름(기본 400)
- 향후 고려: 매우 짧은 snippet(<40자) skip 로직 추가 여부 (현재 미구현)

## 보안
- 사이트 정책 준수, 속도 제한, 크리덴셜 보관(Secrets)

## 통신 프로토콜 (Kafka/Pub/Sub)
- Kafka
  - 발행 토픽: `raw.posts.v1` (파티션 키: `hash(source + url_norm)`)
  - 추가 발행: `summary.events.v1` (파티션 키: `hash("summary:" + raw_id)`)
  - 컨슈머 그룹: `collector-service.{env}` (제어/설정 이벤트 사용 시)
  - 헤더: `trace_id`, `schema_version`, `source`, `channel`, `content_type`, `platform_profile`
  - 전달 보장: at-least-once, 지수 백오프 재시도, DLQ: `raw.posts.dlq`
- Pub/Sub
  - 토픽: `raw-posts`, 추가 `summary-events`

## 실행 작업 매핑 (Execution Task Mapping)
이 문서의 기능 요소를 `detailed-task-breakdown.md`의 표준 작업 ID와 연결하여 구현·추적을 일관화.

핵심 매핑:
- C1 스키마 정의: 상태/이벤트 필드 명세 (현재 '데이터/스토리지' 반영)
- C2 소스 어댑터: changedetection + 향후 커스텀 커넥터 구조 (REST 관리 인터페이스 연계)
- C3 레이트 리미터 & 백오프: 재시도/실패 처리 로직 (관측성 메트릭 실패율과 함께)
- C4 Fingerprint 중복 해시: URL+본문 기반 해시 (중복 기초 필터링 언급 보강)
- C5 Raw 이벤트 발행: `raw.posts.v1` 파이프라인 (Kafka/PubSub 섹션)
- C6 헬스 & 메트릭: 수집율/실패율/지연 노출
- C7 재시도 + DLQ: at-least-once + `raw.posts.dlq` 구성
- C8 Secret 관리: API Key/크리덴셜 보관 (ENV + 시크릿 매니저 추상화 예정)
- C9 배치 vs 스트리밍 토글: 추후 고부하/비용 최적화 (백로그 진입 예정)
- C10 멀티테넌트 소스 쿼터: 소스별/테넌트별 할당량 (백로그)
- C11 소스 구성 UI/관리 API: REST 커넥터 CRUD 확장
- C12 히스토릭 백필: 과거 데이터 재수집 잡
- C13 리전 페일오버: 다중 리전 전략 문서화 (백로그)
- (요약 기능 관련) Summarizer R1-R5 (인덱스/벡터), R6-R8(비용/품질 모니터)와 연동 고려

교차(공통) 의존성:
- X1-X3 Observability(로그/메트릭/트레이스), X5 CI, X7 IaC 모듈, X8 RBAC/권한, X10 비용 모니터

추적 방법:
- 구현 PR 제목에 `[C1][C2]` 등 태그 포함
- 배포 체크리스트: C1–C7 완료 + X1–X3 계측 통과 시 초기 E2E 가능

(이 섹션은 주기적으로 Master Task List 반영하여 업데이트)
