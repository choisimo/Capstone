# sentiment-service

## 개요
- 목적: 3클래스(긍/부/중) 및 8감정 분류 점수 산출.

## 인터페이스
- 이벤트(구독): `clean.posts.v1`
- 이벤트(발행): `scores.sentiment.v1`
- 내부 모델 서빙: Ray Serve/TorchServe/Vertex Endpoint

## 데이터/스토리지
- 결과 저장: ClickHouse/ES(쿼리용), Lake(원천/특징)

## 설정(ENV)
- `MODEL_NAME`, `MODEL_VER`
- `BATCH_SIZE`, `MAX_CONCURRENCY`

## 관측성
- Metrics: 처리지연, 정확도(오프라인), 드리프트 지표

## 통신 프로토콜 (Kafka/Pub/Sub)
- Kafka
  - 구독 토픽: `clean.posts.v1` (파티션 키: `dedup_key`)
  - 발행 토픽: `scores.sentiment.v1` (파티션 키: `post_id`)
  - 컨슈머 그룹: `sentiment-service.{env}`
  - 헤더: `trace_id`, `schema_version`, `source`, `channel`, `content_type`, `platform_profile`, `model_ver`
  - 전달 보장: at-least-once, DLQ: `clean.posts.dlq`, `scores.sentiment.dlq`
- Pub/Sub
  - 구독: `clean-posts`
  - 발행: `scores-sentiment`
  - Attributes: 헤더와 동일 매핑
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md`의 `clean.posts.v1`, `scores.sentiment.v1`
- 보안: Kafka(mTLS+ACL), Pub/Sub(IAM)
- 관측성: Lag/스루풋/에러율 모니터, OTel trace 연계

## 백로그
- 온디맨드/배치 혼합 모드, A/B 라우팅

## 실행 작업 매핑 (Execution Task Mapping)
Sentiment 서비스 기능을 상세 작업(S1–S10)과 연결.

핵심 매핑:
- S1 베이스라인 모델 선택: `MODEL_NAME` / 초기 엔드포인트 기동
- S3 추론 마이크로서비스: 이벤트 소비 + 동기 추론 + 점수 발행
- S2 도메인 어댑트 파인튜닝: 모델 버전 증가 `MODEL_VER` 관리
- S4 신뢰도/캘리브레이션: softmax 후 temperature scaling 지표
- S5 드리프트 추적: 롤링 F1/분포 감시, `drift` 메트릭
- S6 A/B 버전 토글: 모델 버전 라우팅 레이어 (feature flag)
- S7 모델 승격 시 과거 재처리(재발행) 파이프라인
- S8 지연 최적화: ONNX/quantization 실험, latency histogram 비교
- S9 편향 감사: 감정/클래스별 fairness 분포 리포트
- S10 설명가능성: 토큰 saliency/attention 기반 highlight (선택적)

비기능:
- p95 지연, 가용성, rollback 기준 -> Master Task List KPI (F1 ≥0.80) 연결

추적/거버넌스:
- 모델 버전 태깅: `<model>-<major.minor>`
- PR 태그: `[S1][S3]` 등
- 배포 체크: S1,S3,S4,S5 + X1-X3 계측 후 초기 출시
