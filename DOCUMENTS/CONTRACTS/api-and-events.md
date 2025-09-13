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
