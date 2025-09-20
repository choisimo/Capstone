# absa-service

## 개요
- 목적: Aspect 기반 감성(ABSA) 산출 및 근거(evidence span) 추출.

## 인터페이스
- 이벤트(구독): `clean.posts.v1`
- 이벤트(발행): `scores.absa.v1`
- 스키마: `aspect`, `polarity`, `evidence_span`, `model_ver`

## 데이터/스토리지
- 근거 인덱스: ES/VectorDB(옵션)

## 설정(ENV)
- `ASPECT_SET`(정의된 정책 속성 셋)
- `MODEL_NAME`, `MODEL_VER`

## 관측성
- Metrics: 근거 커버리지, 처리지연

## 통신 프로토콜 (Kafka/Pub/Sub)
- Kafka
  - 구독 토픽: `clean.posts.v1` (파티션 키: `dedup_key`)
  - 발행 토픽: `scores.absa.v1` (파티션 키: `post_id`)
  - 컨슈머 그룹: `absa-service.{env}`
  - 헤더: `trace_id`, `schema_version`, `source`, `channel`, `content_type`, `platform_profile`, `model_ver`
  - 전달 보장: at-least-once, DLQ: `clean.posts.dlq`, `scores.absa.dlq`
- Pub/Sub
  - 구독: `clean-posts`
  - 발행: `scores-absa`
  - Attributes: 헤더와 동일 매핑
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md`의 `clean.posts.v1`, `scores.absa.v1`
- 보안: Kafka(mTLS+ACL), Pub/Sub(IAM)
- 관측성: Lag/스루풋/에러율 모니터, OTel trace 연계

## 백로그
- 추출식/분류식 혼합, 라벨링 툴 연계

## 실행 작업 매핑 (Execution Task Mapping)
ABSA 파이프라인 A1–A10.

핵심 매핑:
- A1 Aspect 세트 정의: 정책/영역 카탈로그 + 버전
- A2 전처리/정규화: 토큰화/언어/문장 분리
- A3 모델 추론 래퍼: MODEL_NAME + 모델 버전 관리
- A4 Evidence Span 추출: 시퀀스 태깅/규칙 혼합
- A5 스코어 산출/정규화: polarity → 표준 점수+신뢰도
- A6 Post-Filter: 중복/충돌 aspect 병합
- A7 이벤트 발행: `scores.absa.v1` 헤더/partition key 매핑
- A8 모델 모니터링: 처리지연·커버리지·drift 메트릭
- A9 재처리 파이프라인: 모델 업그레이드 시 재산출
- A10 데이터 품질 검증: evidence span 길이/정합성 규칙

교차 의존성:
- Ingest(IW2–IW4), Tagging(T2), Sentiment(S3), Gateway(G1), Alert(AL2)
- 공통 X1–X3, X5, X7, X10

추적:
- PR 태그 `[A3][A4]`; 초기 기능 컷: A1–A7 + A8
- 모델 교체 시 체크리스트: A3/A8/A9 완료 후 배포
