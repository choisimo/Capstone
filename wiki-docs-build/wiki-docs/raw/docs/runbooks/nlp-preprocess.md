# nlp-preprocess

## 개요
- 목적: 텍스트 정규화, 언어감지, 토큰화/형태소. 분석 서비스 전처리.

## 인터페이스
- 이벤트(구독): `clean.posts.v1`
- 이벤트(발행): (옵션) `features.preproc.v1` 또는 인라인 필드 보강 후 다음 서비스로 전달

## 처리 로직
- 정규화: 이모지/URL/특수기호 처리
- 언어감지: cld3/fasttext
- 형태소/토큰화: Khaiii/Kkma/Okt/HF 토크나이저

## 데이터/스토리지
- 사전/모델 가중치 캐시

## 설정(ENV)
- `LANG_DETECTOR_MODEL`
- `TOKENIZER_NAME`

## 관측성
- Metrics: 처리량, 토큰 수, 지연

## 통신 프로토콜 (Kafka/Pub/Sub)
- Kafka
  - 구독 토픽: `clean.posts.v1` (파티션 키: `dedup_key`)
  - 발행 토픽(옵션): `features.preproc.v1` (파티션 키: `post_id`)
  - 컨슈머 그룹: `nlp-preprocess.{env}`
  - 헤더: `trace_id`, `schema_version`, `source`, `channel`, `content_type`, `platform_profile`
  - 전달 보장: at-least-once, DLQ: `clean.posts.dlq`, `features.preproc.dlq`
- Pub/Sub
  - 구독: `clean-posts`
  - 발행(옵션): `features-preproc`
  - Attributes: 헤더와 동일 매핑
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md` (필요 시 `features.preproc.v1` 추가)
- 보안: Kafka(mTLS+ACL), Pub/Sub(IAM)
- 관측성: Lag/스루풋/에러율 모니터, OTel trace 연계

## 백로그
- 사용자 사전/금칙어 사전 동적 반영

## 실행 작업 매핑 (Execution Task Mapping)
N1–N12 대응.

핵심 매핑:
- N1 언어감지: fastText baseline 도입
- N2 문장/토큰 분할: Sentence splitter + tokenizer pipeline
- N3 불용어/구두점 필터: 구성 가능 리스트
- N4 Lemma/Stem 전략 선택: 모델/라이브러리 플러그형
- N5 커스텀 도메인 사전: 구성 리로드 지원
- N6 임베딩 생성: 오픈소스 모델(HF) 추론 + 캐시 키
- N7 벡터 정규화 & 저장: Vector store write (pre-ingest for RAG/Topic)
- N8 캐싱: 동일 텍스트 해시 기반 skip
- N9 배치 vs 스트리밍 벡터화: Throughput 튜닝 토글
- N10 모델 버전 태깅: 재현성/분석 추적
- N11 길이 가드레일: max token cutoff
- N12 프로파일링: 성능 리포트 생성

교차: R3(벡터 스토어), TM2(주제 모델), S1/S3(감성 모델 입력 형식) 의존

추적: PR 태그 `[N6][N7]` 등, 프로파일링 리포트 저장
