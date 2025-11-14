# absa-service

## 개요
- **목적**: 연금 관련 텍스트의 속성 기반 감성 분석(ABSA), 속성 모델 관리, 페르소나 관리 API 제공.
- **구현**: Java Spring Boot (Web, Validation, Data JPA, Actuator).
- **담당 범위**: `services/java/absa/src/main/java/com/capstone/absa/controller/*`, `service/*`, `repository/*`, `entity/*`, `dto/*`, `resources/application.yml`.
- **운영 프로파일**: 단일 Spring Boot 애플리케이션(포트 8003), Kafka 등 메시지 버스 연동 없음.

## 인터페이스
- **REST (Spring MVC)**
  - ABSA 분석 (`/api/v1/absa/analysis/*`)
    - `POST /api/v1/absa/analysis/analyze`
    - `GET  /api/v1/absa/analysis/history/{contentId}`
    - `POST /api/v1/absa/analysis/batch`
  - 속성(Aspect) 관리 (`/api/v1/absa/aspects/*`)
    - `POST /api/v1/absa/aspects/extract`
    - `GET  /api/v1/absa/aspects/list`
    - `POST /api/v1/absa/aspects/create`
  - 모델 관리 (`/api/v1/absa/models/*`)
    - `GET  /api/v1/absa/models/`
    - `GET  /api/v1/absa/models/{modelId}`
    - `PUT  /api/v1/absa/models/{modelId}`
    - `DELETE /api/v1/absa/models/{modelId}`
    - `POST /api/v1/absa/models/initialize`
  - 페르소나(Persona) 관리 (`/api/v1/personas/*`)
    - `POST /api/v1/personas` (생성)
    - `GET  /api/v1/personas` (목록)
    - `GET  /api/v1/personas/{id}` (단건 조회)
  - 헬스 체크
    - `GET /actuator/health` (Actuator)
    - `GET /health` (단순 상태)

### 응답 스키마
- DTO는 Java record로 정의(`services/java/absa/src/main/java/com/capstone/absa/dto/*`).
- 주요 예시
  - `AnalyzeResponse`, `HistoryResponse`, `BatchAnalyzeResponse`
  - `ExtractResponse`, `AspectListResponse`, `CreateAspectResponse`
  - `ModelListResponse`, `ModelDetailResponse`, `ModelUpdateRequest/Response`, `InitializeResponse`
  - `PersonaCreateRequest`, `PersonaResponse`

## 데이터/스토리지
- **주 저장소**: PostgreSQL (JPA/Hibernate)
  - 엔터티: `AspectModelEntity`, `PersonaEntity` 등
  - 인덱스: `personas.name` 유니크 인덱스 등 DDL로 정의
- **DDL 관리**: dev 프로파일에서 `spring.jpa.hibernate.ddl-auto=update`

## 설정(ENV)
- Compose 서비스명: `absa-service` (포트 8003)
- 주요 환경 변수(Compose → Spring)
  - DB 연결: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
  - JPA: `HIBERNATE_DDL_AUTO=update`
  - 프로필: `SPRING_PROFILES_ACTIVE=dev`

## 의존성
- `build.gradle`
  - `spring-boot-starter-web`, `spring-boot-starter-validation`, `spring-boot-starter-data-jpa`
  - `spring-boot-starter-actuator`, `micrometer-registry-prometheus`
  - `org.postgresql:postgresql`, `lombok`

## 로컬 실행(예시)
- **Docker Compose**
  ```bash
  docker compose -f docker-compose.spring.yml up -d absa-service
  ```
- **헬스 체크**
  - `GET http://localhost:8003/actuator/health`
  - `GET http://localhost:8003/health`

## 관측성
- **로그**: Spring Boot 기본 로깅.
- **헬스 체크**: Actuator `/actuator/health` 노출.
- **메트릭/트레이스**: Prometheus 레지스트리 의존성 포함(엔드포인트 활성화는 환경에 따라 구성).

## 보안
- **인증/인가**: 컨트롤러 단 인증 미구현. API Gateway 또는 상위 레이어에서 보호 필요.
- **비밀 관리**: DB 크리덴셜 등은 환경 변수로 주입.

## SLO/성능
- **목표**: 공식 SLO 미정.
- **특징**: 동기 REST + JPA 기반. 배치 분석 시 요청량에 따른 지연 증가 가능.

## 운영/장애 대응
- **DDL**: dev 프로파일에서 자동 DDL 업데이트.
- **예외 처리**: `@RestControllerAdvice` 글로벌 핸들러(Validation 400, NotFound 404 등).

## 통신 프로토콜
- **주 통신**: HTTP/JSON (동기 REST). Kafka/Pub/Sub 연동 코드 없음.

## 백로그
- SpringDoc(OpenAPI) 도입 및 컨트롤러 @Operation 주석 보강.
- 관측성 강화: Prometheus 지표·구조화 로그 추가.

## 실행 작업 매핑
- 컨트롤러/서비스/리포지토리 책임 분리 (패키지 구조 참고).
- DTO 검증(`jakarta.validation`) 및 글로벌 예외 처리 정책 준수.
