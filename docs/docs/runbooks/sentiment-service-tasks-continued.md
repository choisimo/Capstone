# Sentiment Service Plan (Draft - Continued)

Intended final location: `DOCUMENTS/DEVELOPMENT/sentiment-service-tasks-continued.md`

## Implementation Backlog (Chronological)
1. Create model selection doc (criteria: size, accuracy, license) (Day 1)
2. Scaffold FastAPI service with health routes (Day 1)
3. Implement /infer (sync) endpoint (Day 2)
4. Add JSON schema validation (pydantic) (Day 2)
5. Add metrics (Prometheus) middleware (Day 2)
6. Containerize (Dockerfile multi-stage) (Day 3)
7. Add batch /infer/batch endpoint (Day 3-4)
8. Evaluation script + baseline dataset creation (Day 4)
9. Deploy baseline v1.0 to staging (Day 5)
10. Collect misclassified samples (Week 2 start)
11. Fine-tune pipeline notebook -> scripted (Week 2)
12. Calibration (temperature scaling) (Week 3)
13. Model registry metadata file (JSON) (Week 3)
14. Canary/shadow test harness (Week 3-4)
15. Drift detection job (cron) (Week 4-5)
16. A/B routing logic (feature flag integration) (Week 5)
17. Auto reprocess script (historic IDs) (Week 6)
18. Quantization experiment (FP32 -> INT8) (Week 7)
19. Latency & throughput benchmark report (Week 7)
20. Bias audit dataset curation (Week 7)
21. Bias evaluation + report (Week 8)
22. Explainability saliency prototype (Week 8)
23. Promotion runbook doc (Week 8)

## Environment & Config
Env Vars:
- MODEL_PATH
- MODEL_VERSION
- MAX_TOKENS
- ENABLE_BATCH (flag)
- DRIFT_THRESHOLD
- CALIBRATION_PARAMS_PATH

Feature Flags:
- enable_ab_routing
- enable_quantized_model
- enable_explainability

## Deployment Pipeline Hooks
- Pre-deploy: run evaluation; block if F1 drop >2% vs current
- Post-deploy: warmup request set; record latency baseline
- Drift job: if drift_score > threshold 3 consecutive runs -> notify + flag degrade

## Data Management
- Store evaluation datasets with hash (dataset_name, sha256)
- Log inference metadata (model_version, latency, confidence)
- Retain misclassified samples (anonymized) for 30 days

## Observability Spans
- span: preprocess
- span: model_load
- span: inference_forward
- span: calibration
- span: response_serialize

## Security & Privacy
- Restrict model artifact bucket with least privilege
- Validate input length & content type early
- Rate limit batch endpoint separately

## Promotion Workflow Summary
1. Train candidate -> produce metrics.json
2. Compare vs prod baseline (script)
3. If pass -> tag version, upload artifact, update registry
4. Deploy as canary (10% traffic)
5. Monitor latency, drift metrics 24h
6. Promote 100% & trigger reprocess (if enabled)

## Rollback Criteria
- Latency p95 regression >25%
- F1 drop >2% absolute
- Error rate >2% sustained 15m

(END OF DRAFT)