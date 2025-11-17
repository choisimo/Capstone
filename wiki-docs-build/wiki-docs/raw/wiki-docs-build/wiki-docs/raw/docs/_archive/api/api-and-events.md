# API & Event Contracts

## REST APIs (예시, FastAPI)

### GET /v1/sentiments
- query: `q`, `source[]`, `channel[]`, `from`, `to`, `age_band`, `group_by`(issue|age|channel)
- resp:
```
{
  "summary": {"pos": 0.31, "neg": 0.47, "neu": 0.22},
  "emotions": {"anger":0.21, "fear":0.33, ...},
  "series": [{"ts":"2025-09-01T00:00:00Z","pos":0.3,"neg":0.5,"neu":0.2}],
  "meta": {"hits": 120345, "latency_ms": 320}
}
```

### GET /v1/aspects
- query: `aspect[]`, `from`, `to`, `group_by`
- resp: aspect별 감성 분포, 증거 스팬 예시.

### POST /v1/summarize
- body: `{ query, from, to, k, with_evidence: true }`
- resp: 요약 본문, 근거 문서 링크, 인용 구간.

### GET /v1/topics
- resp: 토픽 목록/용어, 토픽별 추이.

### GET /v1/events/effect
- query: `event_id|ts`, `window=[-7, +14]`
- resp: ITS 추정치, 신뢰구간.

## WebSocket
- `/ws/alerts`: 조기경보 스트림 `{ ts, issue, severity, reason, samples[] }`

## Messaging Standards (Kafka/PubSub)
- Partition keys (Kafka):
  - `raw.posts.v1`: `hash(source + url_norm)`
  - `clean.posts.v1`: `dedup_key`
  - `scores.sentiment.v1`, `scores.absa.v1`, `analytics.topic.v1`: `post_id`
  - `ops.alerts.v1`: `issue`
- Pub/Sub mapping: Kafka `raw.posts.v1` ↔ Pub/Sub `raw-posts` (이하 동일 패턴)
- Headers/Attributes:
  - `trace_id`, `span_id`, `schema_version`, `source`, `channel`, `content_type`, `platform_profile`, (선택) `model_ver`
- Delivery semantics:
  - At-least-once. 컨슈머는 idempotent 처리(`dedup_key`, `post_id`, `model_ver`) 권장.
  - DLQ 네이밍: `<topic>.dlq` 예: `raw.posts.dlq`, `clean.posts.dlq`, `scores.sentiment.dlq`.
- Schema registry:
  - Avro/Protobuf + BACKWARD 호환 규칙. 메시지 헤더에 `schema_version` 포함.

## Event Schemas (Kafka/Protobuf, Pub/Sub 호환)

### raw.posts.v1
- topics: Kafka(`raw.posts.v1`), Pub/Sub(`raw-posts`)
- fields: id(string), source(enum), channel(string), url, author_hash, text, lang, created_at, meta(map)

  권장 optional meta 필드(분석·시각화·페르소나 추정을 위해 추가 수집):
  - url_norm(string): 정규화된 URL (중복 제거 및 키 생성에 사용)
  - platform_profile(string): 수집 프로파일 (예: `public-web`)
  - seed_url(string): 시드 뉴스 URL (연관 데이터 추적용)
  - seed_id(string): 시드 이벤트 ID
  - seed_title(string): 시드 뉴스 제목
  - article_title(string): 본문형 데이터의 기사 제목(가능 시)
  - comment_provider(string): 댓글 제공자 구분 (예: `daum`, `youtube`)
  - likes(number): 공감/좋아요 수
  - dislikes(number): 비공감/싫어요 수
  - sentiment(string): `positive` | `neutral` | `negative` (모델에 따라 값 상이 가능)
  - sentiment_score(number): 0~1 확률/신뢰도 점수
  - keywords(array[string]): 본문/댓글에서 추출된 핵심 키워드(상위 N개)
  - video_id(string), video_title(string): 유튜브 비디오 메타 (채널이 youtube인 경우)
  - author(string): 작성자 표시명(가능 시). 개인정보 이슈 방지를 위해 `author` 대신 상단 `author_hash` 사용 권장

  author_hash 필드:
  - 작성자 식별자(표시명 등)를 `(platform + ':' + author)`로 해시(SHA-256)하여 32-hex prefix 저장
  - 동일 플랫폼 내 동일 작성자의 행위 집계/페르소나 추정에 활용
  - 원문 작성자 표시명은 저장하지 않거나 `meta.author`에 선택 저장(기본 권장: 비저장)

### summary.events.v1
- topics: Kafka(`summary.events.v1`), Pub/Sub(`summary-events`)
- emitted by: collector news_watcher after raw.posts.v1 publish when SUMMARY_ENABLED=1
- fields:
  - id(string): summary event ID (UUID)
  - raw_id(string): 원본 raw.posts.v1 이벤트 id (관계 링크)
  - created_at(string, ISO8601): 생성 시각 UTC
  - summary(string): 본문 요약 (최대 400자 기본)
  - key_points(array[string]): 핵심 문장 최대 5개 (환경변수 SUMMARY_KEYPOINTS_MAX)
  - facts(map): 추출 규칙 기반 엔티티 집합
    - amounts(array[string])
    - ratios(array[string])
    - dates(array[string])
    - orgs(array[string])
  - meta(map):
    - model(string): `heuristic` 또는 LLM 모델명
    - input_chars(number): 입력 본문 길이
    - lang(string): 추정/전달 언어 (기본 ko)
    - seed_url(string|nullable)
    - url_norm(string)
    - topic(string): 키워드/토픽 (NEWS_KEYWORD 또는 SUMMARY_TOPIC)
    - source(string): 원본 source (예: news|web|youtube)
    - channel(string): 원본 channel (article|search|video|comment 등)

환경 변수:
- SUMMARY_ENABLED (기본 1)
- SUMMARY_LLM_ENABLED (기본 0)
- SUMMARY_MAX_CHARS (기본 400)
- SUMMARY_KEYPOINTS_MAX (기본 5)

헤더/Attributes:
- trace_id, schema_version=summary.events.v1, source, channel, content_type=application/json, platform_profile, raw_id

소비자 가이드:
- raw_id로 raw.posts.v1 조인하여 원문/요약 결합
- topic+created_at 윈도 기반 최신 요약 선택 가능
- facts.* 필드들은 정규화/집계 시 선택적 사용

### seed.news.v1
- topics: Kafka(`seed.news.v1`) (기본), Pub/Sub(`seed-news`) (권장 매핑)
- fields:
  - id(string): seed 이벤트 고유 ID (UUID)
  - source(enum): `news`
  - channel(string): `naver` | `daum` (뉴스 소스 구분)
  - url(string): 뉴스 원문 URL
  - author_hash(string): 빈 값 (원문 작성자 미상)
  - text(string): 뉴스 제목 또는 요약 텍스트
  - lang(string): 언어 코드 (미설정 시 빈 값)
  - created_at(string, ISO8601): 생성 시각 (UTC)
  - meta(map):
    - url_norm(string): 정규화된 URL
    - platform_profile(string): 수집 프로파일 (예: `public-web`)
    - title(string): 뉴스 제목
    - keyword(string): 트리거 키워드 (예: `국민연금`)
    - tags(array[string]): `seed` 태그 등

### clean.posts.v1
- topics: Kafka(`clean.posts.v1`), Pub/Sub(`clean-posts`)
- fields: id, text_norm, pii_flags, dedup_key, created_at, source, channel

### scores.sentiment.v1
- topics: Kafka(`scores.sentiment.v1`), Pub/Sub(`scores-sentiment`)
- fields: post_id, label3(enum), label8(enum), scores(map[string]float), model_ver, infer_ts

### scores.absa.v1
- topics: Kafka(`scores.absa.v1`), Pub/Sub(`scores-absa`)
- fields: post_id, aspect(enum: FUNDING, PAYOUT_AGE, CONTRIBUTION_RATE, GUARANTEE, ROI, FAIRNESS_GEN, ...), polarity(enum), evidence_span, model_ver

### analytics.topic.v1
- topics: Kafka(`analytics.topic.v1`), Pub/Sub(`analytics-topic`)
- fields: post_id, topic_id(int), topic_terms(array[string]), score(float)

### ops.alerts.v1
- topics: Kafka(`ops.alerts.v1`), Pub/Sub(`ops-alerts`)
- fields: id, ts, issue, severity(enum: INFO/WARN/CRIT), rule_id, samples(array[string]), metrics(map)

## Auth
- OAuth2 Client Credentials, per-scope 권한(`read:analytics`, `write:alerts` 등)

## 에러 규약
- 표준화 에러포맷: `{ code, message, details?, trace_id }`
