# 서비스 개발 문서 인덱스

본 디렉터리는 MSA 기반 국민연금 온라인 여론 분석 시스템의 각 마이크로서비스 개발 문서를 제공합니다.
전체 아키텍처와 데이터·이벤트 계약은 다음 문서를 우선 참조하세요.

- `DOCUMENTS/ARCHITECTURE/system-architecture.md`
- `DOCUMENTS/ARCHITECTURE/gcp-architecture.md`
- `DOCUMENTS/ARCHITECTURE/frontend-integration.md`
- `DOCUMENTS/CONTRACTS/api-and-events.md`
- `DOCUMENTS/DEVELOPMENT/development-guide.md`
- `DOCUMENTS/DEVELOPMENT/gcp-deployment-runbook.md`, `DOCUMENTS/DEVELOPMENT/linux-deployment-runbook.md`

## 서비스 목록

- `api-gateway.md` — 외부 API 관문, 인증/권한, 데이터 집계 및 캐시, WebSocket 중계(`/ws/alerts`).
- `collector-service.md` — 수집/크롤링 커넥터. changedetection.io 연계 및 Event Bus 게시.
- `dedup-anonymizer.md` — 중복제거·스팸/봇 필터·비식별화(PII 마스킹) 파이프라인.
- `nlp-preprocess.md` — 정규화·형태소·언어감지·토큰화·클린징.
- `sentiment-service.md` — 3클래스/8감정 분류 모델 서빙 및 점수 이벤트 발행.
- `absa-service.md` — 정책 속성(Aspect) 추출 및 aspect별 감성 산출.
- `topic-modeler.md` — LDA/BERTopic 기반 토픽 추출·추이 산출.
- `summarizer-rag.md` — 벡터 검색+LLM 요약/논거 추출(온디맨드 API 중심).
- `event-analysis.md` — ITS/상관 분석 배치·API.
- `alert-service.md` — 임계치/변동성 기반 경보 산출, Slack/메일/WS 연동.
- `dashboard-web.md` — 대시보드 웹앱(프런트엔드) 통합 사양.

## 공통 표준

- 이벤트 토픽(예): `raw.posts.v1`, `clean.posts.v1`, `scores.sentiment.v1`, `scores.absa.v1`, `analytics.topic.v1`, `ops.alerts.v1`.
- 인증: 내부 mTLS(서비스 간), 외부 OAuth2/OIDC(API), API Key(내부 유틸성).
- 관측성: OpenTelemetry(Trace/Metric/Log), Sentry(선택), Prometheus/Grafana/Loki.
- 배포 프로파일: `PLATFORM_PROFILE=gcp|linux-server`.
- 데이터 저장: GCP(GCS/BQ) 또는 Linux(MinIO/ClickHouse), 검색(ES/OpenSearch), 벡터DB(pgvector/Milvus).

## 문서 템플릿

새 서비스 문서는 `_template.md`를 참고하여 작성/확장하세요.
