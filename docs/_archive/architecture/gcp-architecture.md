# GCP 레퍼런스 아키텍처 매핑

## 개요
- 목표: 국민연금 온라인 여론 분석 시스템을 GCP에서 안전하고 확장 가능하게 운영.

## 주요 GCP 서비스 매핑
- 컨테이너 오케스트레이션: GKE Autopilot(권장) 또는 GKE Standard
- 메시지/이벤트: Pub/Sub (Kafka 대체) 또는 Confluent Cloud on GCP
- 데이터 레이크: Cloud Storage (GCS)
- 데이터 웨어하우스/시계열 집계: BigQuery (또는 ClickHouse on GKE)
- 검색/로그 분석: Elastic Cloud on GCP 또는 OpenSearch on GKE, 대안: BigQuery/Vertex Search
- 벡터 DB: AlloyDB + pgvector, 또는 Cloud SQL(Postgres)+pgvector, Milvus on GKE(대안)
- 스케줄러/워크플로: Cloud Composer(Airflow Managed) 또는 GKE 내 Airflow
- 모델 서빙: Vertex AI Prediction 또는 Ray Serve/TorchServe on GKE
- LLM: Vertex AI(Gemini) 또는 외부 API(프록시 경유)
- 모니터링/로그: Cloud Monitoring/Logging, Error Reporting, Trace(OTel 수집기 경유)
- 비밀/키: Secret Manager, KMS
- CI/CD: Cloud Build 또는 GitHub Actions + Workload Identity Federation
- 인증/SSO: Cloud Identity, IAP(옵션), OAuth/OIDC with Identity Platform
- 알림: Cloud Functions/Run + Pub/Sub → Email/Slack(Webhook)

## 네트워크·보안
- VPC: 전용 서브넷(ingress, app, data), Private Service Connect로 관리형 서비스 사설접속.
- Ingress: Cloud Load Balancing + Cloud Armor(WAF), HTTPS, mTLS(서비스간).
- Egress: NAT Gateway, 외부 LLM/API는 VPC-SC 정책 검토.
- 비밀: Secret Manager + KMS; GKE Pod는 Workload Identity로 비밀 접근.
- 데이터: PII 금지 저장, DLP API로 샘플 검증(옵션).

## 데이터 파이프라인 on GCP (Linux 서버 호환 매핑)
1) 수집: Cloud Run(크롤러) → Pub/Sub(`raw-posts`) → Dataflow(옵션) → GCS 원천 버킷
   - Linux: Dockerized 크롤러 → Kafka/Redpanda(`raw.posts.v1`) → MinIO/파일
2) 정제/비식별: Composer DAG → BigQuery 스테이징 → DLP 마스킹 → BQ 정제 테이블
   - Linux: Airflow OSS → ClickHouse 스테이징 → NER/규칙 마스킹 → CH 정제 테이블
3) 분석: 모델 추론(Vertex Endpoints or GKE Serving) → 결과 BQ/ES/VectorDB에 저장
   - Linux: TorchServe/Ray Serve → ClickHouse/ES/pgvector 저장
4) 서빙: API Gateway/Cloud Run(backend) → BigQuery BI Engine/ES 조회 → Next.js Frontend(Cloud Run/Cloud CDN)
   - Linux: Nginx+FastAPI(BFF) → ClickHouse/ES 조회 → Next.js(SSR) on Docker + Nginx Cache
5) 알림: BQ/ES 트리거 잡 → Pub/Sub → Cloud Functions → Slack/메일
   - Linux: ClickHouse/ES 배치 → Kafka → FastAPI Worker/Functions → Slack/메일

## Kafka↔Pub/Sub 브릿징 전략
- 목적: 멀티 환경(dev/stage/prod, GCP↔Linux) 간 이벤트 파이프라인 일관성 유지.
- 방안:
  - Confluent Replicator, MirrorMaker2, Dataflow 커넥터 등으로 단방향/양방향 미러링.
  - Kafka 토픽(`raw.posts.v1`) ↔ Pub/Sub 토픽(`raw-posts`)로 1:1 매핑.
  - 헤더/Attributes 매핑: `trace_id`, `schema_version`, `source`, `channel`, `content_type`, `platform_profile`.
  - 전달 보장: At-least-once, DLQ: `*.dlq` 토픽 병행 운영.
  - 스키마: Schema Registry(Avro/Protobuf) 버전 규칙 BACKWARD, GCP는 Schema Registry 호환 계층 또는 스키마 내장 방식.
- 보안:
  - Kafka: mTLS + ACL, SASL/SCRAM(옵션)
  - Pub/Sub: 서비스 계정 + IAM 역할 최소권한, VPC-SC(옵션)
- 관측성: 브릿지 lag/에러율 대시보드, 재처리(리플레이) 플레이북 준비.

## 운영/관측성
- Cloud Monitoring 대시보드: 파이프라인 SLA, 모델 지연, 비용 지표
- 로깅: OTel Collector → Cloud Logging; 추적: Cloud Trace; 에러: Error Reporting
- 비용: 각 서비스별 경보 정책(예산 알림), LLM 호출/Vertex 비용 추적

## 배치/권장 구성
- 프로젝트 분리: dev/stage/prod, 공유 VPC, 폴더/정책 상속
- 권한: 최소권한 원칙, IAM 조건부 정책(Time/Source constraints)
- 데이터 보존: GCS 버전관리/수명주기, BQ 파티셔닝/클러스터링
