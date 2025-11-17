# api-gateway


## 개요

- **목적**: 대시보드/자동화 클라이언트의 단일 진입점. 내부 마이크로서비스(Analysis·Collector·ABSA·Alert·OSINT 계열) 요청 프록시, 헬스 체크, 예외 처리 제공.
- **담당 범위**: Spring Cloud Gateway (`services/java/gateway/src/main/java/com/capstone/gateway/config/GatewayRoutes.java`, `services/java/gateway/src/main/resources/application.yml`). 인증·레이트 제한·캐시 등 고급 기능은 미구현 상태.


## 인터페이스

- **REST(경로 기반 라우팅)**
  - Analysis Service → `/api/v1/analysis/**`, `/api/v1/sentiment/**`, `/api/v1/trends/**`, `/api/v1/reports/**`, `/api/v1/models/**`
  - Collector Service → `/api/v1/collector/**`, `/sources/**`, `/collections/**`, `/feeds/**`
  - ABSA Service → `/api/v1/absa/**`, `/api/v1/personas/**` (페르소나)
  - Alert Service → `/api/v1/alerts/**`
  - OSINT Orchestrator → `/api/v1/osint-orchestrator/**`, `/tasks/**`, `/dashboard/**`
  - OSINT Planning → `/api/v1/osint-planning/**`, `/api/v1/plans/**`
  - OSINT Source → `/api/v1/osint-source/**`, `/api/v1/sources/**`
- **WebSocket/SSE**: 구현 없음.


### 라우팅 특이 사항

- **ABSA Personas 포워딩**: 게이트웨이는 `/api/v1/personas/**` 요청을 ABSA 서비스로 그대로 포워딩합니다(경로 재작성 없음).
- **Alert 레거시 경로 제거**: `/alerts/**`, `/rules/**`, `/notifications/**` 레거시 경로는 제거됨. 현재는 `/api/v1/alerts/**`만 허용.


## 데이터/스토리지

- **캐시 계층**: 구현 없음. 응답 캐싱·Redis 미사용.
- **내부 상태**: 상태 비보존(stateless) 게이트웨이. 라우팅 설정만 관리.


## 설정(ENV)

- Spring Boot `application.yml` 기반 설정.
  - 서비스 URL 프로퍼티(`services.*-url`): `collector-url`, `analysis-url`, `absa-url`, `alert-url`, `osint-orchestrator-url`, `osint-planning-url`, `osint-source-url`.
  - Docker Compose 환경 변수 매핑: `SERVICES_COLLECTOR_URL`, `SERVICES_ANALYSIS_URL`, `SERVICES_ABSA_URL`, `SERVICES_ALERT_URL`, `SERVICES_OSINT_ORCHESTRATOR_URL`, `SERVICES_OSINT_PLANNING_URL`, `SERVICES_OSINT_SOURCE_URL`.
  - 포트: `PORT` (기본 8080; docker-compose.spring.yml에서 주입).
  - 프로필: `SPRING_PROFILES_ACTIVE=dev`(기본).


## 의존성

- **주요 구성요소**: Spring Boot, Spring Cloud Gateway, Spring Actuator.
- **참고**: 실제 의존성은 `services/java/gateway/build.gradle` 참조.


## 로컬 실행

- **Docker Compose**

  ```bash
  docker compose -f docker-compose.spring.yml up -d api-gateway
  ```

- **포트**: 기본 8080 (`http://localhost:8080`).


## 관측성

- **로그**: Spring Boot 기본 로깅. 별도 logger 설정 없음.
- **메트릭/트레이스**: Prometheus/OpenTelemetry 미연결.
- **헬스 체크**: Actuator `/actuator/health` 노출.


## 보안

- **인증/인가**: 라우터에 인증 없음. API Key/JWT 검증 미구현.
- **CORS**: 모든 Origin 허용. 프로덕션에서는 `ALLOWED_ORIGINS` 제한 필요.
- **전송 보안**: HTTPS/TLS 구성은 외부 인프라(로드밸런서 등) 의존.


## SLO/성능

- 공식 SLO 미정. 프록시 레이어 특성상 하위 서비스 지연에 의존.
- 타임아웃/재시도: 각 프록시에서 Spring Cloud Gateway 기본 타임아웃/재시도 정책 적용.


## 운영/장애 대응

- **에러 매핑**: 다운스트림 타임아웃/연결 실패 등은 Spring Cloud Gateway 기본 에러 핸들링으로 504/503 응답으로 매핑됨.
- **라이프사이클**: 상태 비보존(stateless) 구성. 라우팅 정의는 Spring Bean으로 관리.
- **모니터링**: Actuator 헬스 체크 중심. 추가 Alerting/메트릭 연계는 백로그.


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
