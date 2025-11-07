# alert-service

## 개요
- **목적**: 감성/분석 지표 기반 경보 생성, 알림 채널(Slack, Email, Webhook 등) 팬아웃, 경보 이력 관리.
- **담당 범위**: `app/routers/alerts.py`, `app/routers/rules.py`, `app/routers/notifications.py`, `app/services/alert_service.py`, `app/services/rule_service.py`, `app/services/notification_service.py`, `app/db.py`, `app/schemas.py`.
- **운영 프로파일**: FastAPI 단일 프로세스. 외부 메시지 큐 없이 HTTP/DB 중심.

## 인터페이스
- **REST**:
  - `GET /alerts` · `GET /alerts/{id}` · `POST /alerts` · `PATCH /alerts/{id}` · `DELETE /alerts/{id}` (`app/routers/alerts.py`).
  - `POST /alerts/trigger`, `POST /alerts/bulk-trigger` – 규칙 평가 후 경보 생성.
  - `POST /alerts/{id}/acknowledge`, `POST /alerts/{id}/resolve` – 경보 상태 갱신.
  - `GET /alerts/stats/overview`, `GET /alerts/dashboard/summary` – 통계/대시보드 데이터.
  - `GET /alerts/{id}/history` – 상태 이력.
  - `GET /rules`, `POST /rules`, `PUT /rules/{id}`, `DELETE /rules/{id}` (`app/routers/rules.py`).
  - `POST /rules/{id}/test` – 규칙 시뮬레이션.
  - `GET /notifications`, `POST /notifications/{id}/retry` 등 (`app/routers/notifications.py`).
  - `GET /health`, `GET /` (`app/main.py`).
- **비동기 처리**: `NotificationService` 내부에서 채널별 알림 전송. 현재 Celery 큐 연동은 코드로만 정의돼 있으며 실행체계 별도 구성 필요.

## 데이터/스토리지
- **PostgreSQL** (`app/db.py`):
  - `AlertRule`, `Alert`, `Notification`, `AlertHistory`, `AlertSubscription` 테이블.
  - ENUM은 문자열 열로 저장.
- **Redis**: 설정값 존재(`app/config.py`)하지만 코드 내 직접 사용 경로 없음.
- **Alembic**: `requirements.txt`에 포함되며 마이그레이션 관리 전제.

## 설정(ENV)
- `.env.example` 참고.
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
