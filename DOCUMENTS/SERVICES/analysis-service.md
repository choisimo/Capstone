# analysis-service

## 개요
- **목적**: 텍스트 감성 분석·트렌드 분석·리포트 생성·ML 모델 관리를 제공하는 분석 마이크로서비스.
- **담당 범위**: `app/routers/sentiment.py`, `app/routers/trends.py`, `app/routers/reports.py`, `app/routers/models.py`, `app/services/*`, `app/db.py`.
- **운영 프로파일**: FastAPI 단일 인스턴스. Kafka 등 메시지 버스 연동 없음.

## 인터페이스
- **REST (모든 경로는 `/api/v1` 접두사)**
  - 감성 분석 (`app/routers/sentiment.py`)
    - `POST /api/v1/sentiment/analyze`
    - `POST /api/v1/sentiment/batch`
    - `GET /api/v1/sentiment/history/{content_id}`
    - `GET /api/v1/sentiment/stats`
  - 트렌드 분석 (`app/routers/trends.py`)
    - `POST /api/v1/trends/analyze`
    - `GET /api/v1/trends/entity/{entity}`
    - `GET /api/v1/trends/popular`
    - `GET /api/v1/trends/keywords`
  - 리포트 관리 (`app/routers/reports.py`)
    - `POST /api/v1/reports/generate`
    - `GET /api/v1/reports/`
    - `GET /api/v1/reports/{report_id}`
    - `DELETE /api/v1/reports/{report_id}`
    - `GET /api/v1/reports/{report_id}/download`
  - 모델 관리 (`app/routers/models.py`)
    - `POST /api/v1/models/upload`
    - `GET /api/v1/models/`
    - `GET /api/v1/models/{model_id}`
    - `PUT /api/v1/models/{model_id}/activate`
    - `POST /api/v1/models/train`
    - `GET /api/v1/models/training/{job_id}`
    - `DELETE /api/v1/models/{model_id}`
- **헬스 체크**: `GET /health`
- **의존하는 스키마**: `app/schemas.py` (Pydantic 모델)

## 데이터/스토리지
- **PostgreSQL (`app/db.py`)**
  - `sentiment_analyses`: 개별 감성 분석 결과(`SentimentAnalysis`).
  - `trend_analyses`: 시계열 메트릭과 키워드(`TrendAnalysis`).
  - `reports`: 생성된 리포트(`Report`).
  - `ml_models`: 모델 메타데이터 및 상태(`MLModel`).
- **세션 관리**: `SessionLocal` (autocommit=False, autoflush=False).
- **백그라운드 작업**: FastAPI `BackgroundTasks`를 이용한 비동기 처리 (DB 외 영속화 없음).

## 설정(ENV)
- **로딩 방식**: `app/config.py::Settings` (`pydantic-settings`)가 `.env`에서 로드.
- **주요 환경 변수**
  - `DATABASE_URL` (기본: `postgresql://postgres:password@localhost:5432/pension_sentiment`).
  - `REDIS_URL` (캐시 옵션, 기본 사용 안 함).
  - `DEBUG` (기본 `True`).
  - `SECRET_KEY` (JWT 용. 현 구현에서는 토큰 검증 미사용).
  - `ALLOWED_HOSTS` (CORS/TrustedHost). 기본 `[*]`.
  - 내부 서비스 URL: `API_GATEWAY_URL`, `COLLECTOR_SERVICE_URL`, `ABSA_SERVICE_URL`, `ALERT_SERVICE_URL` (현재 코드에서 직접 호출하지 않음).
  - `ML_MODEL_PATH`, `CACHE_TTL`, `LOG_LEVEL` 등 서비스 동작 파라미터.
- **비밀 관리**: `.env` 예시는 참고용이며, 실제 자격 증명은 Secret Manager/Vault 등 외부 시스템 관리 필요.

## 의존성
- **Python 패키지** (`requirements.txt`)
  - FastAPI 0.104.1, Uvicorn 0.24.0, SQLAlchemy 2.0.23, Pydantic 2.5.0, Pydantic-settings 2.1.0.
  - 데이터 처리: NumPy 1.24.3, Pandas 2.0.3, scikit-learn 1.3.0.
  - ML: Transformers 4.35.0, Torch 2.1.0 (Hugging Face 파이프라인 사용).
  - 기타: Redis 5.0.1, Requests, HTTPX, Celery(향후 확장), pytest 계열.
- **외부 서비스/OSS**
  - Hugging Face Hub (모델 `cardiffnlp/twitter-roberta-base-sentiment-latest`).
  - Redis/ Celery 연계는 설정만 존재하며 현재 코드 경로에서는 사용되지 않음.
- **내부 서비스 의존**: 실 호출 없음. 분석 결과는 API Gateway가 집약.

## 로컬 실행
- **Uvicorn**
  ```bash
  uvicorn app.main:app --reload --port 8001
  ```
- **Docker** (`BACKEND-ANALYSIS-SERVICE/Dockerfile`)
  ```bash
  docker build -t analysis-service .
  docker run --rm -p 8001:8001 --env-file .env analysis-service
  ```
- **개발 모드**: `DEBUG=True` 시 `uvicorn` reload 활성화.

## 관측성
- **로그**: `logging.basicConfig(level=logging.INFO)` (구조화 미적용).
- **헬스 체크**: `/health` 엔드포인트 기본 상태만 반환, DB 연결 검사 없음.
- **메트릭/트레이스**: Prometheus/OpenTelemetry 연동 미구현. 확장 필요.

## 보안
- **인증/인가**: 라우터 단계 인증 미구현. API Gateway 또는 상위 레이어에서 접근 제어 필요.
- **CORS/Trusted Host**: `ALLOWED_HOSTS` 기본 `[*]`. 프로덕션에서는 제한 설정 필수.
- **데이터 보호**: 감성 분석 텍스트가 DB에 평문 저장. 민감 데이터 취급 시 추가 마스킹/암호화 요구.

## SLO/성능
- **공식 SLO 없음**. 현재 구현은 싱글 프로세스 + 동기 DB I/O 기반.
- **성능 특징**
  - 감성 분석은 Hugging Face 파이프라인 동기 호출 → GPU 없이 CPU 추론.
  - 배치 분석(`POST /sentiment/batch`)은 순차 처리. 대량 데이터 시 큐잉 필요.
  - 트렌드 분석은 DB 내 저장 데이터 기준 집계. 범위 설정에 따라 지연 커짐.

## 운영/장애 대응
- **DB 초기화**: `Base.metadata.create_all()`로 서비스 기동 시 테이블 생성.
- **예외 처리**: global exception handler(`app/main.py`)에서 500 응답 통일.
- **재시도**: 배치/알림 큐 등 재시도 로직 미구현. Celery 설정만 존재.
- **백업/아카이브**: DB 레벨 전략 필요 (문서화 미포함).

## 통신 프로토콜
- **주 통신**: HTTP/JSON.
- **이벤트/메시지 버스**: 없음.
- **BackgroundTasks**: 리포트 생성·배치 분석에서 FastAPI 백그라운드 큐 사용.

## 백로그 / 개선 사항
- Hugging Face 모델 로딩 최적화 및 캐시 공유.
- Redis/Celery 기반 비동기 파이프라인 본격화.
- Prometheus metrics 및 구조화 로깅 도입.
- 감성/트렌드 결과 검증(ground truth) 파이프라인 및 재현성 테스트 스위트 작성.
- 인증/인가 미들웨어 추가 및 API 키/토큰 검증 체계 확립.

## 실행 작업 매핑
- **AN1**: 감성 분석 파이프라인 표준화 (`SentimentService.analyze_sentiment`).
- **AN2**: 배치 처리 및 통계 (`SentimentService.batch_analyze_sentiment`, `get_sentiment_statistics`).
- **AN3**: 트렌드 계산 로직 (`TrendService.analyze_trends`, `_calculate_trend`).
- **AN4**: 키워드/엔티티 트렌드 API (`TrendService.get_entity_trends`, `get_trending_keywords`).
- **AN5**: 리포트 생성 (`ReportService.generate_report`).
- **AN6**: 리포트 다운로드/보존 (`ReportService.download_report`).
- **AN7**: 모델 메타 관리 (`MLModelService.upload_model`, `activate_model`).
- **AN8**: 모델 학습 워크플로우 (`MLModelService.train_model`).
- **X1**: 환경 설정 (`app/config.py::Settings`).
- **X2**: 서비스 수명주기 + CORS/TrustedHost 설정 (`app/main.py`).
