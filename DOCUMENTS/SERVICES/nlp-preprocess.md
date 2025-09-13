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
