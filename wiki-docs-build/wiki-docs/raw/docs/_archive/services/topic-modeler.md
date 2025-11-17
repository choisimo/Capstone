# topic-modeler

## 개요
- 목적: 토픽 추출(LDA/BERTopic)과 시계열 추이 산출.

## 인터페이스
- 이벤트(구독): `clean.posts.v1`
- 이벤트(발행): `analytics.topic.v1`

## 데이터/스토리지
- 토픽 용어·가중치 저장, 시계열 머티리얼라이즈드 뷰(ClickHouse)

## 설정(ENV)
- `TOPIC_MODEL=lda|bertopic`
- `EMBEDDING_MODEL`

## 관측성
- Metrics: 토픽 수, 코히런스, 처리지연

## 통신 프로토콜 (Kafka/Pub/Sub)
- Kafka
  - 구독 토픽: `clean.posts.v1` (파티션 키: `dedup_key`)
  - 발행 토픽: `analytics.topic.v1` (파티션 키: `post_id`)
  - 컨슈머 그룹: `topic-modeler.{env}`
  - 헤더: `trace_id`, `schema_version`, `source`, `channel`, `content_type`, `platform_profile`, (선택) `model_ver`
  - 전달 보장: at-least-once, DLQ: `clean.posts.dlq`, `analytics.topic.dlq`
- Pub/Sub
  - 구독: `clean-posts`
  - 발행: `analytics-topic`
  - Attributes: 헤더와 동일 매핑
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md`의 `clean.posts.v1`, `analytics.topic.v1`
- 보안: Kafka(mTLS+ACL), Pub/Sub(IAM)
- 관측성: Lag/스루풋/에러율 모니터, OTel trace 연계

## 백로그
- 동적 토픽 병합/분할, 최신성 가중치

## 실행 작업 매핑 (Execution Task Mapping)
Topic 모델러 관련 작업 TM1–TM8 매핑.

핵심 매핑:
- TM1 코퍼스 샘플링/클리닝: 초기 전처리 파이프라인(Stopwords, 언어 필터) -> Embedding 준비
- TM2 베이스라인(LDA/NMF) 평가: coherence/perplexity 산출
- TM3 코히런스 메트릭 파이프라인: 자동 계산 + 모니터링 대시보드
- TM4 동적 토픽 리프레시(주기적 재빌드): TTL 기반 재계산
- TM5 토픽 라벨 생성: 상위 용어 + 휴리스틱/LLM 라벨러
- TM6 임베딩 기반 클러스터(HDBSCAN) 실험: BERTopic 방식 비교
- TM7 토픽 병합/분할 거버넌스: 품질 기준/관리 API 초안
- TM8 드리프트 로그 & 알람: 토픽 분포 변화 감시

교차 의존성: N6 임베딩, R3 벡터 스토어, Analysis/Explorer 시각화

추적: PR 태그 `[TM2][TM3]`, 대시보드: coherence trend
