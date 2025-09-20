# api-gateway

## 개요
- 목적: 외부 클라이언트(대시보드·자동화) 진입점. 인증/권한, 데이터 집계/캐시, 에러 규약, 레이트 제한, WebSocket 중계 제공.
- 담당 범위: `DOCUMENTS/CONTRACTS/api-and-events.md`에 정의된 `/v1/*`, `/ws/alerts` 노출.

## 인터페이스
- REST
  - `GET /v1/sentiments`
  - `GET /v1/aspects`
  - `GET /v1/topics`
  - `POST /v1/summarize`
  - `GET /v1/events/effect`
- WebSocket
  - `GET /ws/alerts`
- 내부 통신
  - gRPC/REST로 내부 서비스 호출(bff 모드) 또는 데이터 스토어 조회(읽기 최적화·캐시)
- 이벤트
  - (옵션) `ops.alerts.v1` 구독하여 WS로 fan-out

## 데이터/스토리지
- 캐시: Redis(키=쿼리 파라미터 해시)
- 읽기 저장소: ClickHouse/ES/VectorDB 등(읽기 전용 계정)

## 설정(ENV)
- `OAUTH_ISSUER`, `OAUTH_AUDIENCE`, `JWKS_URL`
- `REDIS_URL`
- `READ_DB_URL`(CH/ES/PG)
- `WS_ALERTS_TOPIC`(옵션)

## 의존성
- 내부: sentiment-service, absa-service, topic-modeler, summarizer-rag, event-analysis
- 외부: Redis, ClickHouse/ES/pgvector

## 로컬 실행
- FastAPI 예시: `uvicorn app.main:app --reload --port 8081`
- Compose: `infra/compose`에서 `api-gateway` 서비스 기동

## 관측성
- Metrics: 요청수/지연/오류율, 캐시히트율
- Traces: 각 하위 서비스호출 체인
- Logs: 표준화 에러포맷 `{ code, message, trace_id }`

## 보안
- 외부 OAuth2/OIDC, 내부 mTLS
- 레이트 제한/쿼터, 입력 검증(zod/pydantic)

## 통신 프로토콜 (Kafka/Pub/Sub)
- 목적: 조기경보 WS 팬아웃 및 내부 비동기 요청/응답 패턴(옵션)
- Kafka
  - 구독 토픽(옵션): `ops.alerts.v1` (파티션 키: `issue`)
  - 컨슈머 그룹: `api-gateway.{env}.alerts`
  - 헤더→WS 매핑: `trace_id`, `schema_version`, `issue`, `severity`
  - 전달 보장: at-least-once, DLQ: `ops.alerts.dlq`
- Pub/Sub
  - 구독: `ops-alerts`
  - Attributes: 동일 매핑
- 보안: Kafka(mTLS+ACL), Pub/Sub(IAM)
- 관측성: 컨슈머 lag/WS 전송 실패율, backpressure 제어

## SLO/성능
- P95 응답 < 1s(캐시 적중 시), < 2s(미적중)

## 백로그
- SSE 지원 옵션, GraphQL 게이트 추가 검토

## 실행 작업 매핑 (Execution Task Mapping)
Gateway 기능을 G1–G10 작업 ID로 표준화하여 구현/추적.

핵심 매핑:
- G1 인증 미들웨어: OAuth2/OIDC JWT 검증 + 키 캐시(JWKS) ("보안" 섹션 기반)
- G2 레이트 제한·쿼터: 사용자/Org/IP 단위 버킷 ("보안"/레이트 제한 언급 강화)
- G3 요청 검증: 파라미터/바디 스키마(pydantic/zod) 및 입력 정규화
- G4 응답 캐시 계층: Redis 키=쿼리 파라미터 해시 ("데이터/스토리지" 캐시)
- G5 팬인/Aggregation: 내부 서비스 호출 Fan-in + 오류/지연 병합
- G6 WebSocket Alerts 브릿지: `ops.alerts.v1` 구독 → `/ws/alerts` fan-out
- G7 에러 규약 통합: `{code,message,trace_id}` 포맷 표준화 및 매핑
- G8 관측성 계측: 지연/캐시히트율/오류율 + 업스트림 트레이스 연계
- G9 서킷브레이커/타임아웃/재시도: 하위 서비스 보호 (패턴/백로그 연결)
- G10 라우트 버전 레지스트리: `/v1/*` 정의 및 감가(deprecation) 메타 태그

교차 의존성:
- Sentiment(S1–S*), ABSA(A*), Topic(TM*), Summarizer(R*), Event-Analysis(EA8), Alert(AL4–AL10)
- 공통 X1(로그) X2(메트릭) X3(트레이스) X5(CI) X8(RBAC) X10(비용)

추적:
- PR 태그 예: `[G1][G4]` ; 초기 GA 기준: G1–G4 + G7 + G8 충족
- 캐시 효과성: G4 완료 후 P95 개선율/캐시히트율 대시보드화
- 안정화 단계에서 G9 활성 (에러율/타임아웃 임계 도달 시)
