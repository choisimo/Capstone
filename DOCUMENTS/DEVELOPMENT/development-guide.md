# 개발 가이드

## 1. 저장소 구조(제안, MSA 모듈형)
- infra/: IaC(K8s manifests, Helm, ArgoCD)
- services/
  - collector-service/
  - dedup-anonymizer/
  - nlp-preprocess/
  - sentiment-service/
  - absa-service/
  - topic-modeler/
  - summarizer-rag/
  - event-analysis/
  - api-gateway/
  - dashboard-web/
- libs/
  - common-schemas/
  - data-utils/
  - ml-utils/
- data-pipelines/
  - airflow-dags/
  - spark-jobs/
- docs/
  - PRD/, ARCHITECTURE/, CONTRACTS/, DEVELOPMENT/

## 2. 로컬 개발 환경
- 요구: Python 3.10+, Node 18+, Docker, Make, Poetry/uv, pnpm.
- 플랫폼 프로파일: `PLATFORM_PROFILE=gcp|linux-server` 환경변수로 동작 분기.
- 명령 예시
  - Python: `poetry install && poe dev`
  - Front: `pnpm i && pnpm dev`
  - Docker: `docker compose --profile $PLATFORM_PROFILE up -d`

## 3. 데이터 파이프라인
- Airflow 로컬: Docker Compose, `airflow/dags`에 DAG 배치. (GCP는 Cloud Composer 권장)
- 메시지 브로커: (GCP) Pub/Sub 에뮬레이터 또는 서비스 / (Linux) Redpanda/Kafka 단일 노드.

## 4. 모델 개발
- 데이터셋 버전: DVC/LakeFS, MLflow로 실험 추적.
- 파인튜닝: HF Transformers, Pytorch Lightning; 한국어 PLM(KoBERT/KoELECTRA) + 도메인 어댑테이션.
- 배포: TorchServe/Ray Serve, A/B 라우팅(env flag, header 기반).

## 5. RAG
- 임베딩: KoSimCSE/Multilingual-E5, pgvector로 인덱스.
- 프롬프트: 동적 템플릿 저장소(JSON5), 정책문서 메타 포함.

## 6. 품질·테스트
- 유닛/통합/계약 테스트(pytest + schemathesis), CDC(Schema Registry) 테스트.
- 데이터 품질: Great Expectations, 일일 리포트.

## 7. 보안·컴플라이언스
- 시크릿: Vault/Secrets Manager. 접근 최소화, 감사 로그.
- 로깅: PII 금지, 비식별 토큰 사용.

## 8. CI/CD
- GitHub Actions: lint/type/test/build, 이미지 빌드, 매니페스트 배포.
- 배포 타겟: (GCP) GKE/Cloud Run + Workload Identity Federation / (Linux) 자체 K8s 또는 단일 VM Docker Compose.
- PR 체크: 계약 테스트, 성능 회귀 체크(샘플 배치).

## 9. 운영
- 모니터링: (GCP) Cloud Monitoring/Logging/Trace 또는 (Linux) Prometheus, Loki, Tempo, Sentry.
- 캐시·비용: Redis, 호출 레이트 제한, LLM 캐시. (GCP) 예산 알림, (Linux) Grafana Alerting.
- 백업·재처리: (GCP) BQ/GCS 스냅샷·DAG / (Linux) ClickHouse/파일 스냅샷, 리플레이 DAG.

---

## 로컬 인프라 빠른 시작
- 환경 파일 준비:
  - `cp DOCKER/.env.example DOCKER/.env`
- 인프라 기동:
  - `docker compose -f DOCKER/docker-compose.yml --env-file DOCKER/.env up -d`
- 호스트에서 마이크로서비스 연결 값:
  - `MONGO_URI=mongodb://localhost:27017`
  - `MONGO_DB=analysis`
  - `VECTOR_DB_URL=postgresql://postgres:postgres@localhost:5432/vectors`
  - `KAFKA_BROKERS=localhost:19092`
  - `MESSAGE_BUS=kafka`
- 컨테이너 내부(동일 네트워크)에서 연결 값:
  - `MONGO_URI=mongodb://mongodb:27017`
  - `VECTOR_DB_URL=postgresql://postgres:postgres@pgvector:5432/vectors`
  - `KAFKA_BROKERS=redpanda:9092`

## 환경 변수 매트릭스(요약)
- Analysis Service (`BACKEND-ANALYSIS-SERVICE`)
  - 필수: `MONGO_URI`, `MONGO_DB`
  - VectorDB: `VECTOR_DB_URL` 또는 `VECTOR_DB_HOST|PORT|USER|PASSWORD|DATABASE`
  - LLM: `GEMINI_API_KEY`(옵션)
  - 튜닝: `MESH_CACHE_TTL_SEC`, `MAX_MESH_NODES`, `MAX_MESH_LINKS`, `AGG_MIN_SUPPORT`, `RAG_MAX_TOKENS`
  - 로드 방식: Pydantic BaseSettings가 작업 디렉토리의 `.env` 자동 로드
- Ingest Worker (`workers/ingest_worker.py`)
  - 필수: `MONGO_URI`, `MONGO_DB`, `KAFKA_BROKERS`
  - 그룹/토픽: `INGEST_GROUP`, `RAW_TOPIC`, `SEED_TOPIC`, `CLEAN_TOPIC`, `SCORES_TOPIC`
  - 관측/안정성: `INGEST_METRICS_PORT`(Prometheus), `SENTRY_DSN`
- Collector Service (`BACKEND-WEB-COLLECTOR`)
  - 버스 선택: `MESSAGE_BUS=auto|kafka|pubsub`
  - Kafka: `KAFKA_BROKERS=localhost:19092`, `RAW_TOPIC=raw.posts.v1`
  - Pub/Sub: `PUBSUB_PROJECT=...`, `RAW_TOPIC=raw-posts`
  - 외부: `CHANGEDETECTION_BASE_URL`, `CHANGEDETECTION_API_KEY`
  - 옵션: Perplexity `PPLX_*`, 브릿지 동작 `POLL_INTERVAL_SEC`, `INCLUDE_HTML`, `WATCH_TAG`, `SOURCE`, `CHANNEL`, `PLATFORM_PROFILE`

## 서비스 실행 예시
- Analysis API: `uvicorn BACKEND-ANALYSIS-SERVICE/app.main:app --reload --port 8010`
- Ingest Worker: `python BACKEND-ANALYSIS-SERVICE/workers/ingest_worker.py`
- Collector Bridge: `python -m BACKEND-WEB-COLLECTOR.bridge`
