# analysis-service

## 개요

- **목적**: 텍스트 감성 분석·트렌드 분석·리포트 생성·ML 모델 관리를 제공하는 분석 마이크로서비스.
- **구현**: Java Spring Boot (Web, Validation, Data JPA, Actuator).
- **담당 범위**: `services/java/analysis/src/main/java/com/capstone/analysis/controller/*`, `service/*`, `repository/*`, `dto/*`, `resources/application.yml`.
- **운영 프로파일**: 단일 Spring Boot 애플리케이션(포트 8001), 메시지 버스 연동 없음.

## 인터페이스

- **REST (모든 경로는 `/api/v1` 접두사)**
  - 감성 분석 (SentimentController)
    - `POST /api/v1/sentiment/analyze`
    - `POST /api/v1/sentiment/batch`
    - `GET  /api/v1/sentiment/history/{contentId}`
    - `GET  /api/v1/sentiment/stats`
  - 트렌드 분석 (TrendController)
    - `POST /api/v1/trends/analyze`
    - `GET  /api/v1/trends/entity/{entity}`
    - `GET  /api/v1/trends/popular`
    - `GET  /api/v1/trends/keywords`
  - 리포트 관리 (ReportController)
    - `POST /api/v1/reports/generate`
    - `GET  /api/v1/reports/`
    - `GET  /api/v1/reports/{reportId}`
    - `DELETE /api/v1/reports/{reportId}`
    - `GET  /api/v1/reports/{reportId}/download`
  - 모델 관리 (ModelController)
    - `POST /api/v1/models/upload`
    - `GET  /api/v1/models/`
    - `GET  /api/v1/models/{modelId}`
    - `PUT  /api/v1/models/{modelId}/activate`
    - `POST /api/v1/models/train`
    - `GET  /api/v1/models/training/{jobId}`
    - `DELETE /api/v1/models/{modelId}`
- **헬스 체크**: `GET /actuator/health`

## 데이터/스토리지

- **PostgreSQL (JPA/Hibernate)**
- 엔터티/리포지토리 구성은 서비스 코드 참조.

## 설정(ENV)

- Compose → Spring 매핑
  - DB: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
  - JPA: `HIBERNATE_DDL_AUTO=update`
  - 프로필: `SPRING_PROFILES_ACTIVE=dev`

## 의존성

- `build.gradle`
  - `spring-boot-starter-web`, `spring-boot-starter-validation`, `spring-boot-starter-data-jpa`, `spring-boot-starter-actuator`
  - `org.postgresql:postgresql`

## 로컬 실행

- **Docker Compose**

  ```bash
  docker compose -f docker-compose.spring.yml up -d analysis-service
  ```

## 관측성

- **로그**: Spring Boot 기본 로깅.
- **헬스 체크**: Actuator `/actuator/health` 노출.
- **메트릭/트레이스**: 기본 미구현(추가 구성 필요).

## 보안

- **인증/인가**: 컨트롤러 단 인증 미구현. API Gateway 등 상위 레이어 제어 필요.

## SLO/성능

- **공식 SLO 없음**. 동기 REST + JPA I/O 기반.

## 운영/장애 대응

- **DDL**: dev 프로파일 `hibernate.ddl-auto=update`.

## 통신 프로토콜

- **주 통신**: HTTP/JSON.
- **이벤트/메시지 버스**: 없음.

## 백로그 / 개선 사항

- SpringDoc OpenAPI 도입 및 컨트롤러 주석 보강.
- Prometheus metrics 및 구조화 로깅 도입.

## 실행 작업 매핑

- 컨트롤러/서비스/리포지토리 책임 분리 (패키지 구조 참고).
