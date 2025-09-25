# api-gateway

## 개요
- **목적**: 대시보드/자동화 클라이언트의 단일 진입점. 내부 마이크로서비스(Analysis·Collector·ABSA·Alert·OSINT 계열) 요청 프록시, 헬스 체크, 예외 처리 제공.
- **담당 범위**: `app/main.py`, `app/routers/*.py`, `app/config.py`. 인증·레이트 제한·캐시 등 고급 기능은 미구현 상태.

## 인터페이스
- **REST**
  - `GET /health` — 각 마이크로서비스 `/health` 호출 후 상태 집계.
  - `GET /` — 게이트웨이 메타 정보 및 라우팅 대상 목록.
  - `app/routers/analysis.py` → `/api/v1/analysis/*` (감성/트렌드/리포트/모델 API 프록시).
  - `app/routers/collector.py` → `/api/v1/collector/*` (수집 서비스 프록시).
  - `app/routers/absa.py` → `/api/v1/absa/*` (ABSA 서비스 프록시).
  - `app/routers/alerts.py` → `/api/v1/alerts/*` (경보 서비스 프록시).
  - `app/routers/osint_orchestrator.py` → `/api/v1/osint-orchestrator/*`.
  - `app/routers/osint_planning.py` → `/api/v1/osint-planning/*`.
  - `app/routers/osint_source.py` → `/api/v1/osint-source/*`.
- **WebSocket/SSE**: 구현 없음.
- **내부 통신**: 각 라우터가 `httpx.AsyncClient`로 하위 서비스 REST 호출.

## 데이터/스토리지
- **캐시 계층**: 구현 없음. 응답 캐싱·Redis 미사용.
- **내부 상태**: FastAPI lifespan에서 `app.state.http_client` 초기화만 수행.

## 설정(ENV)
- **로딩 방식**: `app/config.py::Settings` (`pydantic-settings`).
- **주요 환경 변수**
  - `PORT` (기본 `8000`), `DEBUG` (기본 `True`).
  - 서비스 URL: `ANALYSIS_SERVICE_URL`, `COLLECTOR_SERVICE_URL`, `ABSA_SERVICE_URL`, `ALERT_SERVICE_URL`, `OSINT_ORCHESTRATOR_SERVICE_URL`, `OSINT_PLANNING_SERVICE_URL`, `OSINT_SOURCE_SERVICE_URL`.
  - 타임아웃: `DEFAULT_TIMEOUT` (기본 30초), `HEALTH_CHECK_TIMEOUT` (기본 5초 — 실제 코드에서는 별도 사용 없이 상수화된 값으로 5초 지정).
  - 레이트 제한/인증 관련 필드(`RATE_LIMIT_PER_MINUTE`, `JWT_*`)는 선언만 되어 있고 코드상 사용 없음.
  - CORS 설정: `ALLOWED_ORIGINS`, `ALLOWED_METHODS`, `ALLOWED_HEADERS` (기본 `*`).
- **비밀 관리**: JWT 시크릿 등 민감 값은 환경 변수로 주입. 현재 기능 미구현.

## 의존성
- **Python 패키지**: FastAPI, httpx, pydantic-settings, uvicorn (`BACKEND-API-GATEWAY/requirements.txt`).
- **외부 서비스**: 실제로는 각 내부 마이크로서비스 HTTP 엔드포인트.
- **사용하지 않는 항목**: Redis, Prometheus, JWT 인증은 코드에 없음.

## 로컬 실행
- **Uvicorn**
  ```bash
  uvicorn app.main:app --reload --port 8000
  ```
- **Docker**: `Dockerfile`는 Python 기반 컨테이너에서 FastAPI 실행.
  ```bash
  docker build -t api-gateway .
  docker run --rm -p 8000:8000 --env-file .env api-gateway
  ```
- **Compose**: `docker-compose.*.yml`에서 `api-gateway` 서비스 정의 확인 필요 (환경 변수로 각 서비스 URL 주입).

## 관측성
- **로그**: FastAPI/uvicorn 기본 로깅. 별도 logger 설정 없음.
- **메트릭/트레이스**: Prometheus/OpenTelemetry 미연결.
- **헬스 체크**: `/health` 호출 시 개별 서비스 상태/응답 시간만 기록.

## 보안
- **인증/인가**: 라우터에 인증 없음. API Key/JWT 검증 미구현.
- **CORS**: 모든 Origin 허용. 프로덕션에서는 `ALLOWED_ORIGINS` 제한 필요.
- **전송 보안**: HTTPS/TLS 구성은 외부 인프라(로드밸런서 등) 의존.

## SLO/성능
- 공식 SLO 미정. 프록시 레이어 특성상 하위 서비스 지연에 의존.
- 타임아웃/재시도: 각 프록시에서 httpx 타임아웃 기반. 재시도·서킷브레이커·캐시는 미구현.

## 운영/장애 대응
- **예외 처리**: `httpx.TimeoutException`→504, `httpx.ConnectError`→503, 기타 예외→500.
- **라이프사이클**: lifespan에서 httpx 클라이언트 생성/종료 관리.
- **모니터링**: 헬스 체크 외 자동화 없음. Alerting은 외부 시스템 필요.

## 통신 프로토콜
- **주 통신**: HTTP/JSON 프록시.
- **이벤트/Kafka**: 코드에 없음.
- **WebSocket**: `/ws/alerts` 미구현.

## 백로그 / 개선 사항
- 인증/레이트 제한 미들웨어 추가.
- 요청/응답 로깅 표준화 및 트레이싱 연동.
- 공통 에러 스키마/성공 응답 래퍼 적용.
- Redis 기반 응답 캐시/서킷브레이커 도입.
- WebSocket 팬아웃(알림) 혹은 SSE 도입 여부 검토.

## 실행 작업 매핑
- **G1**: 인증 미들웨어 (미구현 → 백로그).
- **G2**: 레이트 제한 (미구현 → 백로그).
- **G3**: 요청 검증 (FastAPI 스키마로 부분 적용).
- **G4**: 응답 캐시 (미구현).
- **G5**: 마이크로서비스 프록시 (`app/routers/*.py`).
- **G6**: WebSocket Alerts (미구현).
- **G7**: 에러 규약 (`app/main.py`의 예외 핸들러).
- **G8**: 관측성 (헬스 체크 수준).
- **G9**: 타임아웃/재시도 (`httpx.AsyncClient(timeout=...)`).
- **G10**: 라우트 버전 관리 (`/api/v1/*`).
