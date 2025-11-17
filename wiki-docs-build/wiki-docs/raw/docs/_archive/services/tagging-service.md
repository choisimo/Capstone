# tagging-service

## 개요
- 목적: Gemini(Function Calling) 기반 감정/페르소나/경험 태깅 및 원인 설명 생성.
- 담당 범위: `documents` 텍스트 입력→ 다중 태그 산출, 휴리스틱+LLM 하이브리드.
- 운영 프로파일: `PLATFORM_PROFILE=gcp|linux-server`

## 인터페이스
- 이벤트(구독): `clean.posts.v1` 또는 내부 큐(`documents` 신규)
- 이벤트(발행): (
  옵션) `scores.sentiment.v1`(요약 점수), `tags.semantic.v1`(신규 정의)
- REST: (
  옵션) `POST /v1/tag` 배치 태깅
- 스키마: `DOCUMENTS/CONTRACTS/api-and-events.md` + 본 문서(`tags.semantic.v1` 제안)

## 태깅 스키마 제안
- `tags.semantic.v1`
  - fields: `post_id`, `sentiment3`(pos|neg|neu), `emotions`(map: anger, fear, joy,...), `persona[]`(e.g., civil_servant, retiree, youth), `experience[]`(e.g., application_delay, payout_confusion), `keywords[]`, `explanations[]`(free text), `model_ver`, `infer_ts`

## 데이터/스토리지
- MongoDB: `documents.meta` 업데이트(태그 반영)
- VectorDB: 키워드/태그 임베딩(옵션)

## 설정(ENV)
- 필수: `GEMINI_API_KEY`
- 선택: `MODEL_VER`, `BATCH_SIZE`, `MAX_CONCURRENCY`, `ON_FAIL=retry|skip`, `CACHE_TTL_SEC`

## 의존성
- 내부 서비스: ingest-worker(입력), analysis-service(소비자)
- 외부 서비스/OSS: Google Gemini, tenacity(재시도), OpenTelemetry

## 로컬 실행(예시)
- 배치 워커: `python services/tagging_worker.py` (예시)

## 관측성
- Metrics: `tags/sec`, `llm_latency_ms`, `cache_hit`, `error_rate`, `skip_rate`
- Traces: LLM 호출 span, 프롬프트/함수콜 메타만 기록(본문은 PII/비밀 제외)
- Logs: 태그 요약/모델 버전/샘플 결과

## 보안
- 인증/인가: 내부망 제한
- 비밀/키 관리: Secret Manager/Vault
- 데이터: 본문 최소한 전달, PII 제거

## SLO/성능
- 처리량: 5–20 rps(LLM 한도 내 확장)
- 지연: 태그 지연 P95 < 2.5s(배치), 오류율 < 1%

## 운영/장애 대응
- 재시도/백오프: LLM 오류 지수백오프+회로차단기, 부분 성공 기록
- 폴백: 휴리스틱 태깅만으로 다운그레이드 모드

## 통신 프로토콜 (Kafka/Pub/Sub)
- Kafka/PubSub는 선택. 기본은 DB 업데이트 pull 기반.
- 헤더 전파: `trace_id` 유지

## 백로그
- 사용자 피드백 기반 태그 수정 루프, 라벨셋 버저닝/온톨로지 문서화

## 실행 작업 매핑 (Execution Task Mapping)
Tagging 관련 Detailed Task Breakdown 태그(T1–T7)와의 연결.

핵심 매핑:
- T1 규칙 기반 부트스트랩: 휴리스틱/키워드 스캐폴드
- T2 다중 라벨 분류 베이스라인: 초기 ML/LLM Hybrid
- T3 임계값 최적화: Precision/Recall 조정 스크립트
- T4 계층적 태그 그룹 구성: ontology/parent-child 매핑
- T5 피드백 엔드포인트: 승인/거절 API 저장 후 재학습 큐
- T6 재학습 스케줄러: 주기/성능 조건 기반 트리거
- T7 Zero-shot 확장 실험: 임시 태그 확장 벤치마크

교차 의존성: N6 임베딩(키워드 벡터), S1/S3 감성 점수(입력 메타), Analysis-service 소비

추적: PR 태그 `[T2][T3]`, 메트릭 대시보드 `tags/sec`/`llm_latency_ms`
