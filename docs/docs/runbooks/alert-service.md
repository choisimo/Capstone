# alert-service

## 개요

- **목적**: 감성/분석 지표 기반 경보 관리 및 간단한 규칙 토글 API 제공.
- **구현**: Java Spring Boot (Web, Actuator, JPA 설정 존재하나 현재 컨트롤러는 메모리 스텁 수준).
- **담당 범위**: `services/java/alert/src/main/java/com/capstone/alert/controller/*`, `resources/application.yml`.

## 인터페이스

- **REST (모든 경로는 `/api/v1/alerts` 접두사)**
  - 목록 조회
    - `GET /api/v1/alerts` → 경보 리스트(현재 빈 목록 스텁)
  - 상태 변경
    - `POST /api/v1/alerts/{id}/acknowledge`
    - `POST /api/v1/alerts/{id}/resolve`
  - 규칙 관리(간단 토글)
    - `GET  /api/v1/alerts/rules`
    - `PATCH /api/v1/alerts/rules/{id}` (본문의 `enabled` 또는 `is_active` 반영)
- **헬스 체크**
  - `GET /actuator/health`
  - `GET /health`

## 데이터/스토리지

- 현재 컨트롤러는 스텁 구현으로 DB 연동 없음. `application.yml`에는 PostgreSQL 구성이 존재하며, 향후 확장 시 JPA 연동을 고려.

## 설정(ENV)

- Compose 서비스명: `alert-service` (포트 8004)
- 데이터베이스 환경 변수 (Compose → Spring)
  - `DATABASE_URL`, `DATABASE_USER`, `DATABASE_PASSWORD`
- 헬스 인디케이터
  - 메일 인디케이터 비활성화: `management.health.mail.enabled=false` (적용됨)
- **필수**: `DATABASE_URL`.
- **선택**: `REDIS_URL`, Slack/Twilio/SMTP 크리덴셜, `SERVICE_NAME`, `RATE_LIMIT_PER_MINUTE`, `ENABLE_METRICS`, 외부 서비스 URL 등.
- **보안**: API 키/비밀번호는 Secret Manager/Vault 주입. 저장소에 평문 금지.

## 의존성
- **Python 패키지**: FastAPI, SQLAlchemy, Pydantic, Redis, Celery, httpx, Slack SDK, Twilio, Jinja2, Prometheus-client, Structlog 등 (`requirements.txt`).
- **외부 서비스**: Slack Webhook/API, 이메일 SMTP, Twilio(옵션).
- **내부 서비스**: Analysis/Collector/ABSA 서비스 URL 설정 존재하나 현재 라우터에서 직접 호출하지 않음.

## 로컬 실행
- **Uvicorn**:
  ```bash
  uvicorn app.main:app --reload --port 8004
  ```
- **Docker** (`BACKEND-ALERT-SERVICE/Dockerfile`):
  ```bash
  docker build -t alert-service .
  docker run --rm -p 8004:8004 --env-file .env alert-service
  ```
- **Celery 워커 (옵션)**: 알림 재시도 로직에 Celery 사용 계획이 있으므로 별도 워커 필요 시 `celery -A app.worker worker` 형태 구성.

## 관측성
- **헬스 체크**: `/health` 단일 엔드포인트. DB 검사 없음.
- **메트릭**: Prometheus 노출 설정만 존재 (`ENABLE_METRICS`, `METRICS_PORT`), 실제 엔드포인트 정의 필요.
- **로깅**: `structlog` + 표준 logging 사용 (`app/services/notification_service.py`).

## 보안
- **인증/인가**: REST 엔드포인트에 인증 절차 미구현. API Gateway 레이어에서 보호해야 함.
- **비밀/키 관리**: Slack/Twilio/SMTP 키는 환경 변수로 주입.
- **CORS**: 모든 Origin 허용(`app/main.py`). 프로덕션에서 제한 필요.

## SLO/성능
- 공식 SLO 정의 없음. 설정값으로 `RATE_LIMIT_PER_MINUTE`, `MAX_ALERTS_PER_HOUR`, 채널별 rate limit 적용 가능.
- 대량 알림 처리 시 Celery/비동기 채널로 확장 권장.

## 운영/장애 대응
- **재시도**: `NotificationService`에서 채널별 재시도 및 backoff 구현 (`retry_delays`, `max_retries`).
- **히스토리**: `AlertHistory`에 상태 변경 기록.
- **쿨다운**: 규칙별 `cooldown_minutes`로 중복 경보 제한.
- **구독 관리**: `AlertSubscription` 모델 기반 사용자별 구독 설정.

## 통신 프로토콜
- **주 통신**: REST/HTTP + 이메일/Slack/Webhook. Kafka 등 메시지 버스 미사용.
- **알림 채널**: 이메일(SMTP), Slack API, Webhook, Twilio SMS(비활성 기본).

## 백로그
- Prometheus/OTel 메트릭 실 구현.
- 인증 미들웨어 추가(API 키 또는 OAuth2).
- Redis 캐시 활용(쿨다운 관리 등) 여부 결정.
- Celery 워커 실행 파이프라인 정비.
- Alert-Analysis 연계(자동 트리거 호출) 구현.

## 실행 작업 매핑
- **AL1**: 규칙 CRUD (`app/routers/rules.py`, `app/services/rule_service.py`).
- **AL2**: 입력 스트림 어댑터 → 현재 HTTP 요청 기반(`POST /alerts/trigger`).
- **AL3**: 누락 – 지표 계산 로직은 외부 서비스에서 제공.
- **AL4**: `AlertService.evaluate_rule` 내 조건 평가.
- **AL5**: `NotificationService`의 rate limit 및 재시도 설정.
- **AL6**: Slack/Email/Webhook notifier (`app/services/notification_service.py`).
- **AL7**: 심각도는 규칙 정의 시 선택(`AlertRule.severity`).
- **AL8**: 통계/대시보드 (`AlertService.get_alert_stats`, `get_dashboard_data`).
- **AL9**: AlertHistory 기반 재처리 트래킹.
- **AL10**: 규칙 버전/수정 기록은 created_by/updated_at 필드 활용.
