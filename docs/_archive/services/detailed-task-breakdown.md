# Detailed Task Breakdown (Draft in SERVICES)

Intended final location: `DOCUMENTS/DEVELOPMENT/detailed-task-breakdown.md`
Move after review.

Legend: P0 (Launch Critical), P1 (Launch Important), P2 (Post-Launch Enhancement), P3 (Nice-to-Have). Each task includes an indicative effort (S < 1d, M 1–3d, L 4–7d, XL > 7d) and dependencies.

---
## 1. Collector Service
- C1: Define ingestion schema (events, raw_message, source_meta) (P0, S)
- C2: Implement source adapters (RSS, API, Webhook abstraction) (P0, M) dep: C1
- C3: Rate limiting & backoff policy module (P0, S)
- C4: Dedup fingerprint (hash(title+source+published_at)) (P0, S) dep: C1
- C5: Persist raw events to staging topic/queue (P0, S)
- C6: Health & metrics (ingest/sec, failures, lag) (P0, S)
- C7: Retry & poison queue pattern (P0, M) dep: C5
- C8: Secure credentials via Secret Manager (P0, S)
- C9: Batch flush vs streaming tradeoff toggle (P1, M)
- C10: Multi-tenant source quotas (P2, M) dep: C2
- C11: Source config UI integration contract (P2, M)
- C12: Backfill historical loader (P2, L)
- C13: Regional failover plan (P3, M)

## 2. Dedup & Anonymizer
- D1: Canonicalization (lowercase, strip HTML, normalize punctuation) (P0, S)
- D2: Shingling + MinHash / SimHash experiment baseline (P0, M)
- D3: Adjustable similarity threshold config (P0, S) dep: D2
- D4: PII regex pass (emails, phones, IDs) (P0, S)
- D5: PII ML-based NER scrub (fallback if regex fails) (P1, M)
- D6: Hash salt rotation + key mgmt doc (P1, S)
- D7: Metrics (duplicates %, avg cluster size) (P0, S)
- D8: Benchmark perf with 10k docs batch (P1, S) dep: D2
- D9: Adaptive threshold via feedback loop (P2, L) dep: D7
- D10: GDPR deletion request pipeline (P2, M)

## 3. NLP Preprocess
- N1: Language detection (fastText or langid) baseline (P0, S)
- N2: Sentence segmentation & tokenization pipeline (P0, S)
- N3: Stopword & punctuation configurable filters (P0, S)
- N4: Lemmatization/stemming strategy selection (P0, S)
- N5: Custom domain dictionary integration (P1, M)
- N6: Embedding generation (open-source model) (P0, M) dep: N1,N2
- N7: Vector normalization + storage (P0, S) dep: N6
- N8: Caching layer for repeated texts (P1, S)
- N9: Batch vs streaming vectorization toggle (P1, S)
- N10: Model version tagging & audit (P1, S)
- N11: Guardrails: max length truncation (P0, S)
- N12: Profiler run and latency budget doc (P1, S)

## 4. Sentiment Service
- S1: Baseline sentiment model selection (P0, S)
- S2: Domain adaptation fine-tune plan (P1, M) dep: S1
- S3: Inference microservice (REST + batch endpoint) (P0, M) dep: S1
- S4: Confidence scoring & calibration (P1, S)
- S5: Drift tracking (rolling F1 vs baseline) (P1, M)
- S6: A/B toggling model versions (P2, M)
- S7: Auto reprocess on model upgrade (P2, M) dep: S6
- S8: Latency optimization (quantization/pruning) (P2, M) dep: S3
- S9: Bias audit (demographic / sector) (P2, L)
- S10: Explainability (saliency / top tokens) (P3, M)

## 5. ABSA (Aspect-Based Sentiment)
- A1: Define aspect taxonomy (domain-specific) (P0, S)
- A2: Data labeling spec & sampling plan (P0, S)
- A3: Prototype aspect extractor (seq2seq or span) (P1, M)
- A4: Joint sentiment per aspect classification (P1, M) dep: A3
- A5: Evaluate macro F1 per aspect (P1, S)
- A6: Active learning loop design (P2, M)
- A7: Cold-start fallback to keyword heuristics (P1, S) dep: A1
- A8: Confidence threshold tuning script (P2, S)
- A9: Aspect drift detection (frequency delta) (P2, M)
- A10: Consolidated aspect alias mapping (P2, S)

## 6. Tagging Service
- T1: Rule-based bootstrap tags (P0, S)
- T2: Multi-label classifier baseline (P1, M)
- T3: Threshold optimization (precision floor) (P1, S)
- T4: Hierarchical tag grouping (P2, M)
- T5: Feedback endpoint (accept/reject) (P2, S)
- T6: Retraining schedule automation (P2, S)
- T7: Zero-shot tag expansion prototype (P3, M)

## 7. Topic Modeler
- TM1: Corpus sampling & cleaning job (P0, S)
- TM2: Baseline (LDA / NMF) evaluation (P0, M)
- TM3: Coherence metrics pipeline (P0, S) dep: TM2
- TM4: Dynamic topic refresh (weekly) (P1, S)
- TM5: Topic label generator (top terms + heuristics) (P1, S)
- TM6: Embedding-based clustering (HDBSCAN) experiment (P1, M)
- TM7: Merge/split topic governance (P2, M)
- TM8: Topic drift log & alerts (P2, S)

## 8. Summarizer (RAG)
- R1: Define retrieval index schema (P0, S)
- R2: Chunking strategy evaluation (size vs recall) (P0, S)
- R3: Vector store integration (FAISS/PGVector) (P0, M)
- R4: Baseline abstractive summarizer (open model) (P0, M)
- R5: Prompt templating & guardrails (P0, S)
- R6: Hallucination detection heuristics (P1, M)
- R7: Citation linking to source docs (P1, S)
- R8: Cost & latency budget instrumentation (P1, S)
- R9: Long context optimization (window packing) (P2, M)
- R10: Multi-document synthesis improvements (P2, M)

## 9. Event Analysis Service
- EA1: Define event taxonomy + severity (P0, S)
- EA2: Pattern detectors (regex + ML hybrid) (P0, M)
- EA3: Temporal correlation (sliding window aggregator) (P1, M)
- EA4: Entity resolution integration (P1, S)
- EA5: Scoring function (impact * confidence) (P1, S)
- EA6: Alert emission contract (P0, S)
- EA7: Replay mode for post-mortems (P2, M)
- EA8: Anomaly detection baseline (stats) (P2, M)
- EA9: Graph-based correlation experiment (P3, M)

## 10. Alert Service
- AL1: Subscription model (user, filter criteria) (P0, S)
- AL2: Delivery channels abstraction (email, webhook, Slack) (P0, M)
- AL3: Rate limiting per user/org (P0, S)
- AL4: De-dup alert window (P0, S)
- AL5: Retry with exponential backoff (P0, S)
- AL6: Template engine for alert formatting (P1, M)
- AL7: Quiet hours & escalation rules (P1, M)
- AL8: Severity-based channel routing (P1, S)
- AL9: Alert analytics (CTR, latency) (P2, S)
- AL10: On-call override UI integration (P3, M)

## 11. Mesh Aggregator
- M1: Input stream fan-in design (P0, S)
- M2: Backpressure handling (P0, S)
- M3: Partitioning key strategy (P0, S)
- M4: Enrichment lookups (cache + DB) (P1, M)
- M5: Event schema version translation (P1, S)
- M6: Priority lanes (critical vs bulk) (P1, M)
- M7: Late event handling logic (P2, S)
- M8: Adaptive load shedding (P2, M)
- M9: Cross-region replication (P3, L)

## 12. Analysis Service
- AN1: Query DSL definition (P0, S)
- AN2: Aggregation operators (count, avg, distinct) (P0, M)
- AN3: Time window functions (P0, S)
- AN4: Caching layer (hot queries) (P1, M)
- AN5: AuthZ filters integration (P0, S)
- AN6: Query planner cost metrics (P2, M)
- AN7: Materialized views for heavy patterns (P2, L)
- AN8: Multi-tenant resource quotas (P2, M)
- AN9: Query tracing & sampling (P2, S)

## 13. API Gateway
- G1: Routing rules & service registry (P0, S)
- G2: AuthN (JWT/OAuth) baseline (P0, S)
- G3: AuthZ (role + org scoping) (P0, M) dep: G2
- G4: Rate limiting middleware (P0, S)
- G5: Request/response schema validation (P0, S)
- G6: Circuit breaker + retries (P1, M)
- G7: Observability (trace headers pass-through) (P0, S)
- G8: Canary release support (P2, M)
- G9: API analytics export (P2, S)
- G10: Developer portal auto-doc (P3, M)

## 14. Dashboard Web
- W1: Auth integration & session handling (P0, S)
- W2: Core layout, nav, theming (P0, S)
- W3: Real-time updates (WebSocket/SSE) baseline (P1, M)
- W4: Data visualization components (charts) (P1, M)
- W5: Accessibility audit (P1, S)
- W6: Performance budgets (LCP < 2.5s) (P1, S)
- W7: Offline fallback (P2, M)
- W8: Feature flag wiring (P1, S)
- W9: Error boundary patterns (P0, S)
- W10: UI test harness (P1, M)
- W11: SSO integration (P2, M)

## 15. Ingest Worker
- IW1: Consumer concurrency tuning (P0, S)
- IW2: Idempotent processing (P0, S)
- IW3: Batch vs single dispatch config (P0, S)
- IW4: Dead-letter requeue tool (P1, S)
- IW5: Latency histogram metrics (P0, S)
- IW6: Graceful shutdown drain (P0, S)
- IW7: Schema evolution handling (P1, S)
- IW8: Priority queue support (P2, M)
- IW9: Adaptive concurrency scaling (P2, M)

## Cross-Cutting (Observability, Security, DevOps)
- X1: Central logging structure & fields spec (P0, S)
- X2: Distributed tracing baseline (P0, S)
- X3: Metrics taxonomy (service.*) (P0, S)
- X4: Secret rotation policy doc (P0, S)
- X5: CI pipeline with unit + lint + security scan (P0, M)
- X6: Staging environment parity checklist (P0, S)
- X7: Infra IaC baseline modules (network, compute, secrets) (P0, M)
- X8: RBAC roles + principle of least privilege (P0, S)
- X9: Pen test & threat model outline (P1, M)
- X10: Cost monitoring & budgets (P1, S)

---
## Dependency Highlights
- API Gateway (G1–G5) precedes Dashboard data integration (W3–W4)
- Collector & Dedup complete before Preprocess embeddings (C1–C5 before N6)
- NLP embeddings (N6–N7) must land before Summarizer retrieval (R3–R4)
- Sentiment baseline (S1,S3) needed for ABSA (A3–A4) evaluation synergy

## Initial Critical Path (Launch)
Collector (C1–C7) -> Dedup (D1–D3,D7) -> NLP (N1–N7) -> Sentiment (S1,S3) -> API Gateway (G1–G5) -> Dashboard (W1,W2,W9) -> Observability (X1–X3) -> Security (G2,G3,X4,X8) -> Deployment (X5,X7)

---
## Risk & Mitigation Summary
- Model Drift (S5, TM4): Early metric instrumentation.
- Data Quality (C2, D2): Hash+similarity redundancy.
- Latency Spikes (M2, IW1): Backpressure + adaptive concurrency.
- Vendor Lock (R4): Open model baseline + abstraction layer.
- Cost Escalation (R4, N6): Cost metrics (R8, X10) from day 1.

(END OF DRAFT)