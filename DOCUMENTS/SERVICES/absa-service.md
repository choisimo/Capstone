# absa-service

## 개요
- **목적**: 수집된 연금 관련 텍스트에 대해 규칙 기반 Aspect 감성 분석과 페르소나 인사이트 API를 제공한다.
- **담당 범위**: `app/routers/analysis.py`, `app/routers/aspects.py`, `app/routers/models.py`, `app/routers/personas.py`, `app/services/absa_service.py`, `app/services/persona_analyzer.py`, `app/db.py`.
- **운영 프로파일**: 단일 FastAPI 프로세스(컨테이너 기반), 외부 Kafka 연동 없음.

## 인터페이스
- **REST (FastAPI)**:
  - `POST /analysis/analyze` (`app/routers/analysis.py::analyze_absa`): 요청 `{"text": str, "aspects": [str]?, "content_id": str?}`. 규칙 기반 스코어 계산 후 `absa_analyses` 테이블에 저장. `confidence`는 현재 난수 기반(`random.uniform`).
  - `GET /analysis/history/{content_id}` (`get_analysis_history`): 특정 `content_id`의 분석 이력 반환.
  - `POST /analysis/batch` (`batch_analyze`): 여러 요청을 순차 실행. 내부에서 `analyze_absa` 호출.
  - `POST /aspects/extract` (`app/routers/aspects.py::extract_aspects`): 등록된 키워드 기반 속성 후보 반환. 키워드 매칭 실패 시 기본 속성 세트 반환.
  - `GET /aspects/list` (`list_aspects`): 활성 속성 모델 목록 조회.
  - `POST /aspects/create` (`create_aspect`): 신규 속성 모델 생성.
  - `GET /models/` / `GET /models/{id}` / `PUT /models/{id}` / `DELETE /models/{id}` / `POST /models/initialize` (`app/routers/models.py`): 속성 정의 CRUD.
  - `GET /api/v1/personas/{user_identifier}/analyze` (`app/routers/personas.py::analyze_persona`): 사용자 히스토리 기반 페르소나 프로파일 생성.
  - `GET /api/v1/personas/network/{user_id}` (`get_persona_network`): 사용자 네트워크 그래프 반환.
  - `GET /api/v1/personas/{persona_id}/details` (`get_persona_details`): 페르소나 상세 및 최근 게시물/연결 정보.
  - `POST /api/v1/personas/{user_identifier}/track` (`track_user_activity`): 활동 로그 저장 및 비동기 페르소나 갱신 예약.
  - `POST /api/v1/personas/connections/update` (`update_user_connections`): 사용자 간 상호작용 강도 갱신.
  - `GET /api/v1/personas/trending` (`get_trending_personas`): 최근 활동량 기준 트렌딩 페르소나 조회.
  - `GET /health` (`app/main.py::health_check`): 서비스 상태 확인.
  - `GET /` (`app/main.py::root`): 지원 엔드포인트 나열.

## 데이터/스토리지
- **주 저장소**: PostgreSQL (`app/db.py`, `app/models.py`).
  - `app/db.py::ABSAAnalysis`, `AspectModel` 등은 규칙 기반 분석 결과와 속성 정의를 저장.
  - `app/models.py`의 `UserPersona`, `UserConnection`, `Content`, `Comment`, `UserActivity`, `TrendingTopic`, `DataSource`, `ABSAAnalysis` 모델은 페르소나 및 콘텐츠 메타데이터를 관리.
- **인덱스/보관 정책**: SQLAlchemy 모델에 정의된 인덱스(`Index(...)`) 사용. 별도 TTL 정책 없음.

## 설정(ENV)
- **필수**: `PORT`(기본 8003), `DATABASE_URL`.
- **선택**: `DEBUG`, `REDIS_URL`, `ANALYSIS_SERVICE_URL`, `MAX_CONCURRENT_REQUESTS`, `REQUEST_TIMEOUT`, `MODEL_CACHE_SIZE`, `ASPECT_EXTRACTION_CONFIDENCE`, `SENTIMENT_CONFIDENCE`.
- **로딩 방식**: `app/config.py::Settings`가 `pydantic-settings`를 통해 `.env`(.env.example 참조)에서 읽어온다.
- **보안**: 비밀번호/키는 환경 변수 또는 Secret Manager로 주입해야 하며 저장소에 커밋 금지.

## 의존성
- **내부 서비스**: 직접 호출하는 마이크로서비스 없음(게이트웨이가 프록시).
- **외부 서비스/OSS**:
  - PostgreSQL (필수).
  - 선택 Redis(미사용 상태지만 설정 값 존재).
- **Python 패키지**: FastAPI, SQLAlchemy, Pydantic, NumPy, Pandas, scikit-learn, transformers, Torch, httpx, Celery 등 (`requirements.txt` 참조).

## 로컬 실행(예시)
- **Uvicorn**:
  ```bash
  uvicorn app.main:app --reload --port 8003
  ```
- **Docker** (`BACKEND-ABSA-SERVICE/Dockerfile`):
  ```bash
  docker build -t absa-service .
  docker run --rm -p 8003:8003 --env-file .env absa-service
  ```

## 관측성
- **로그**: Python `logging` 사용 (`app/services/absa_service.py`, `app/routers/personas.py` 등). 구조화 미적용.
- **헬스 체크**: `/health` 엔드포인트에서 단순 상태만 반환. DB 연결 검사 없음.
- **메트릭/트레이스**: Prometheus/OTel 계측 미구현. 필요 시 FastAPI 미들웨어로 확장.

## 보안
- **인증/인가**: 라우터 단에 인증 없음. API Gateway 또는 외부 레이어에서 보호 필요.
- **비밀 관리**: `.env.example` 참조. 실제 값은 Secret Manager/Vault 등에서 주입.
- **데이터 보호**: 페르소나 ID는 해시(`PersonaAnalyzer._generate_user_id`)로 생성하여 직접 식별자를 저장하지 않는다.

## SLO/성능
- **목표**: 공식 SLO 미정.
- **현재 구현 특징**: 감성 스코어는 규칙 및 사전 기반(`ABSAService`)이며 `confidence`는 난수 가중치. 대량 요청은 순차 처리하므로 CPU 부하에 주의.

## 운영/장애 대응
- **시작 시 처리**: `Base.metadata.create_all`로 필요한 테이블 자동 생성.
- **실패 대응**: DB 커밋 예외 발생 시 FastAPI가 500으로 전파. 재시도/백오프 없음.
- **백그라운드 작업**: `track_user_activity`가 `BackgroundTasks`를 사용해 페르소나 갱신 예약.

## 통신 프로토콜
- **주 통신**: HTTP/JSON (동기 REST). Kafka/Pub/Sub 연동 코드 없음.
- **헤더/트레이싱**: 표준 trace id 전달 로직 없음.

## 백로그
- **규칙 기반 한계**: 분석 스코어 난수 요소 제거 및 실제 ML 모델 연계 필요.
- **관측성 강화**: Prometheus 지표·구조화 로그 추가.
- **캐시**: Redis 설정을 활용한 모델/결과 캐시 도입.
- **데이터 품질**: ABSA 분석 결과와 페르소나 프로파일의 일관성 검증 로직 보강.

## 실행 작업 매핑
- **A1**: `app/services/absa_service.py::_load_aspect_keywords`에서 도메인 키워드 정의.
- **A2**: `ABSAService._preprocess_text` 및 `_calculate_overall_sentiment`.
- **A3**: `app/routers/analysis.py::_analyze_aspect_sentiment` 규칙 기반 스코어링.
- **A4**: `app/db.py::ABSAAnalysis` 저장 로직.
- **P1**: `app/services/persona_analyzer.py::PersonaAnalyzer.analyze_user_persona`.
- **P2**: `app/routers/personas.py::get_persona_network` 그래프 계산.
- **X1**: `app/config.py::Settings` 환경 설정 관리.
- **X2**: `app/main.py` 라우터 등록 및 CORS/헬스 체크.
