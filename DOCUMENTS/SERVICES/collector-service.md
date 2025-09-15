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
    - Kafka: `KAFKA_BROKERS=localhost:9092`, `RAW_TOPIC=raw.posts.v1`(기본)
    - Pub/Sub: `PUBSUB_PROJECT=my-gcp-project`, `RAW_TOPIC=raw-posts`(기본)
  - 옵션: `POLL_INTERVAL_SEC=60`, `INCLUDE_HTML=0|1`, `WATCH_TAG=태그명`, `SOURCE=web`, `CHANNEL=changedetection`, `PLATFORM_PROFILE=public-web`
  - Perplexity 사용 시: `PPLX_API_KEY=...`(필수), `PPLX_MODEL`(옵션)
- 상태 저장: `.collector_state.json`(기본, 위치 변경은 `COLLECTOR_STATE_PATH`)

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

## 검색 엔진 통합 (Perplexity + changedetection)

프록시/크롤링 외에 빠른 이슈 검색을 위해 Perplexity AI API를 통합했습니다. 변경 감지 검색(changedetection)과 Perplexity 기반 웹 검색 중 선택하거나, Perplexity 미설정/오류 시 자동으로 changedetection으로 폴백합니다.

### REST API
- `GET /api/v1/agent/search`
  - 쿼리 파라미터
    - `q` (필수): 검색 질의어
    - `engine` (기본 `cd`): `cd`(changedetection) | `pplx`(Perplexity)
    - `top_k` (기본 10, 1~50): 결과 개수 제한 (Perplexity)
    - `partial` (기본 false): 부분 일치 (changedetection 전용)
    - `tag` (옵션): 태그 필터 (changedetection 전용)
  - 응답 (정규화된 공통 포맷)
    ```json
    {
      "engine": "pplx|cd",
      "results": [
        {
          "title": "...",
          "url": "https://...",
          "snippet": "...",
          "score": 0.92,
          "source": "perplexity|changedetection",
          "uuid": "... (cd 전용)"
        }
      ],
      "warning": "Perplexity not available, fell back to changedetection.",
      "reason": "... (옵션)"
    }
    ```

### 사용 예시
- Perplexity로 5건 검색
  ```bash
  curl "http://localhost:8001/api/v1/agent/search?q=연금+개편+논쟁&engine=pplx&top_k=5"
  ```
- changedetection에서 태그로 필터 후 검색
  ```bash
  curl "http://localhost:8001/api/v1/agent/search?q=example.com&engine=cd&tag=News"
  ```
