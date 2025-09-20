# dedup-anonymizer

## 개요
- 목적: 중복 제거, 스팸/봇 필터, PII 비식별화. `raw.posts.v1` → `clean.posts.v1`.

## 인터페이스
- 이벤트(구독): `raw.posts.v1`
- 이벤트(발행): `clean.posts.v1`
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md`

## 처리 로직
- 중복: URL+해시/MinHash, 윈도우링(시간)
- 스팸/봇: 휴리스틱+ML(옵션)
- 비식별: NER+규칙, `author_hash`만 유지

## 데이터/스토리지
- 룰/사전: 키워드/정규식/블랙리스트
- 감사로그: 비식별 변환 결과(샘플)

## 설정(ENV)
- `WAREHOUSE=clickhouse|bigquery`
- `CLEAN_TOPIC=clean.posts.v1`

## 관측성
- Metrics: 제거율, 비식별 검출율, 처리지연

## 보안
- PII 저장 금지, 샘플링 검증 시 마스킹

## 통신 프로토콜 (Kafka/Pub/Sub)
- Kafka
  - 구독 토픽: `raw.posts.v1` (파티션 키: `hash(source + url_norm)`)
  - 발행 토픽: `clean.posts.v1` (파티션 키: `dedup_key`)
  - 컨슈머 그룹: `dedup-anonymizer.{env}`
  - 헤더: `trace_id`, `schema_version`, `source`, `channel`, `content_type`, `platform_profile`
  - 전달 보장: at-least-once, DLQ: `raw.posts.dlq`, `clean.posts.dlq`
- Pub/Sub
  - 구독: `raw-posts`
  - 발행: `clean-posts`
  - Attributes: 헤더와 동일 매핑
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md` 참조
- 보안: Kafka(mTLS+ACL), Pub/Sub(IAM)
- 관측성: Lag/스루풋/에러율 모니터, OTel trace 연계

## 백로그
- DLP API(GCP) 통합 옵션

## 실행 작업 매핑 (Execution Task Mapping)
기능을 D1–D10 작업과 연계.

핵심 매핑:
- D1 정규화/전처리: 중복 해시 일관성 확보
- D2 MinHash/SimHash 실험: 유사문서 군집 초기
- D3 임계값 설정 기능: 구성 파일/ENV 스위치
- D4 PII 정규표현식 스크러빙: 이메일/전화/NID
- D5 ML NER 기반 PII 확장: 휴리스틱 실패 fallback
- D6 Hash Salt/Key Rotation: 보안/프라이버시 강화
- D7 메트릭: 중복율/클러스터 크기/PII 검출
- D8 벤치마크: 10k 문서 배치 처리 성능 측정
- D9 적응형 임계값: 피드백 루프(중복 false positive 감소)
- D10 GDPR 삭제 파이프라인: 특정 hash 제거 재처리

교차 의존성: C1–C5 (Collector 출력 품질), X1–X3 관측성, X4 비밀회전 정책

추적: PR 제목 `[D2][D3]` 등, 메트릭 대시보드 확인 후 D9 시작
