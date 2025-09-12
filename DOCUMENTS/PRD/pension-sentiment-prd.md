# PRD: 국민연금 온라인 여론 AI 감성분석 및 정책 피드백 시스템

## 1. 배경 및 문제 정의
- 초저출산·고령화로 인한 기금 소진 전망(2055년), 보험료율·소득대체율 조정에 대한 사회적 갈등 심화.
- 기존 정형 설문은 시의성·입체성 부족. 온라인 비정형 데이터(뉴스 댓글, 커뮤니티, SNS)에 잠재된 고해상도 정서 신호를 체계적으로 수집·분석할 필요.

## 2. 목표 (Outcome-oriented)
- 실시간 여론 감성 측정 → 정책 설계·소통 전략에 직결되는 인사이트 제공.
- 핵심 지표: (1) 감성 F1≥0.85 (긍/부/중), (2) 8종 감정 분류 Macro-F1≥0.80, (3) 정책 이벤트 인과효과 추정의 신뢰 구간 보고, (4) 조기경보 민감도/특이도 기준 충족(운영 기준 협의).

## 3. 범위 (In/Out)
- In: 데이터 크롤링/수집 파이프라인, 전처리·비식별화, ABSA/다차원 감성, 토픽 모델링, RAG 요약·논거 추출, 이벤트 스터디(ITS), 대시보드, 알림.
- Out: 오프라인 설문 설계·운영, 개인식별 데이터 저장, 비한국어 데이터 대규모 처리.

## 4. 사용자와 페르소나
- 정책결정자: 요약 인사이트, 위험 신호, 브리핑 레포트 자동화.
- 정책분석가/리서처: 세부 쿼리, 필터, 다운로드, 모델 성능 관리.
- 커뮤니케이션 담당: 이슈·세대별 메시지 가이드, 콘텐츠 아이템.
- 데이터엔지니어/ML엔지니어: 파이프라인 상태, 모델/인덱스 배포, A/B.

## 5. 핵심 기능 (Must/Should/Could)
- Must
  - 데이터 수집: 포털 댓글, 커뮤니티, X, 블로그/API 연계. Airflow 주기 스케줄링. 중복·노이즈 제거, 비식별화.
  - 감성/감정 분석: PLM 파인튜닝(KoBERT/KoELECTRA 등), 다차원 감정(≥8종), ABSA.
  - LLM 보강: RAG 기반 논거 추출·요약, 동적 프롬프팅 탐색.
  - 토픽 모델링: LDA/BERTopic, 시계열 추이.
  - 이벤트 분석: 상관·ITS, 정책 발표 대비 감성 변화 추정.
  - 시각화: 이슈·채널·세대별 분포/추이, 드릴다운 필터, 대시보드 공유.
  - 조기경보: 임계치/변동성 기반 알림, 룰/ML 혼합.
- Should
  - 모델 앙상블·지연비용 최적화, 온디맨드 LLM 활용(gemini-2.5-flash-preview-05-20 등).
  - 데이터 카탈로그/계보(데이터 품질 메트릭 포함).
- Could
  - 담론 네트워크 분석(댓글 상호작용 그래프), 키 인플루언서 탐지.

## 6. 비기능 요구사항
- 보안/개인정보: 비식별화 파이프라인, 최소수집, 접근통제, 키 관리(Secret Manager).
- 성능: 일 100만행 수집·처리, 분석 지연 P95 < 10분(배치 기준), 대시보드 응답 < 2초(캐시 포함).
- 신뢰성: 파이프라인 가용성 99.5%, 재처리/역추적 가능.
- 비용: GPU/LLM 호출 비용 모니터링, 월 예산 경보.
- 거버넌스: 모델/데이터 버전관리, 재현 가능한 ML 파이프라인.

## 7. 성공 지표(KPI)
- 모델: F1(3클래스/8감정), ABSA 정확도, 토픽 코히런스.
- 운영: 수집커버리지, 결측·중복률, 파이프라인 실패율, MTTR.
- 비즈니스: 조기경보 유효 경보율, 정책 브리핑 채택 사례 수, 커뮤니케이션 KPI 개선.

## 8. 가정과 제약
- 각 채널의 이용약관 준수 및 로봇배제정책 고려. 공개 데이터·공식 API 우선.
- LLM 호출은 보안 경유지(프록시)와 키 보관 표준 준수.

## 9. 마일스톤(예시, 24주)
- W1-3: 데이터 소스 온보딩, 스키마, POC 크롤러.
- W4-6: Airflow 파이프라인, 전처리·비식별, 데이터 품질 대시보드.
- W7-10: 감성/감정 파인튜닝 v1, ABSA v1, 오프라인 평가.
- W11-14: RAG 인덱스·요약, 토픽 모델링, 대시보드 v1.
- W15-18: ITS/이벤트 스터디, 조기경보 룰, 알림 연계.
- W19-22: 확장·최적화(앙상블, 캐시, 비용), 모니터링.
- W23-24: 시범 운영, 성능 튜닝, 운영 문서화.

## 10. 의존성
- Airflow/Kafka/ClickHouse(or BigQuery)/Elasticsearch·OpenSearch/Vector DB(Milvus, pgvector 등), Grafana/Metabase, ML 스택(PyTorch, HuggingFace, Ray), LLM API(Gemini 등).

## 11. 리스크 및 대응
- 크롤링 차단/법적 리스크 → API/제휴 우선, 요청 속도 제한, 법무 리뷰.
- 개인정보 포함 가능 → 비식별화 규칙·NER 마스킹, 샘플링 점검.
- 모델 편향/드리프트 → 지속적 재학습, 휴리스틱·휴먼인루프 검증.
- 비용 급증 → 캐시·샘플링·온디맨드 LLM, 경보.

## 12. 승인 기준(Exit Criteria)
- 오프라인 평가 충족(F1 기준), 실데이터 대시보드 동작, 첫 조기경보 시나리오 E2E 검증, 운영·보안 점검서 통과.

## 13. 배포 프로파일 및 호환성(GCP-first, Linux 서버 호환)
- 운영환경 프로파일: `gcp`, `linux-server` 두 가지를 공식 지원.
- 공통 기능 동일성: 기능·API·지표는 두 프로파일 간 동등해야 하며, 차이는 성능/비용/운영 자동화 수준에서만 발생.
- 구성 매핑
  - Compute: GKE Autopilot/Cloud Run ↔ Docker Compose + systemd (단일/다중 노드)
  - Event Bus: Pub/Sub ↔ Kafka/Redpanda
  - Data Lake/DW: GCS + BigQuery ↔ MinIO(or POSIX) + ClickHouse
  - Vector DB: AlloyDB/Cloud SQL + pgvector ↔ PostgreSQL + pgvector
  - Scheduler: Cloud Composer ↔ Airflow OSS(Docker)
  - Model Serving: Vertex AI Prediction ↔ TorchServe/Ray Serve
  - Monitoring/Logging: Cloud Monitoring/Logging ↔ Prometheus+Grafana+Loki
  - Secrets: Secret Manager+KMS ↔ Vault 또는 .env(+file permissions)
  - Auth: Identity Platform/Cloud IAP ↔ Keycloak/Ory Hydra
  - CDN/Edge: Cloud CDN ↔ Nginx+Caching(또는 Cloudflare)
- 설정 토글(예):
  - `PLATFORM_PROFILE=gcp|linux-server`
  - `MESSAGE_BUS=pubsub|kafka`
  - `WAREHOUSE=bq|clickhouse`
  - `VECTOR_DB=alloydb|pgvector`
  - `AUTH_PROVIDER=identity-platform|keycloak`
- 추가 수용 기준
  - `linux-server` 프로파일에서 Docker Compose 기준 E2E 시나리오(수집→분석→대시보드→알림)가 단일 VM(8vCPU/32GB)에서 2시간 데이터 배치로 동작.
  - GCP 프로파일에서 동일 시나리오가 스케일 아웃 및 조기경보 실시간 처리(지연 60s 이내)를 충족.
