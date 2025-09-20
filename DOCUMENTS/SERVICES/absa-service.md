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
  -# ABSA Service (Aspect-Based Sentiment Analysis)

## Overview

ABSA Service는 텍스트를 Aspect(관점) 단위로 분해하여 각 관점별 감성을 분석하는 고급 감성 분석 서비스입니다. 연금 관련 텍스트에서 다양한 관점(수익률, 안정성, 접근성 등)에 대한 세분화된 감성을 파악할 수 있습니다.

### 주요 기능
- Aspect 추출 (Entity Recognition)
- Aspect별 감성 분석
- Opinion 추출 및 연결
- 다중 Aspect 처리
- 도메인 특화 모델 (Pension-specific)
- 계층적 Aspect 분석

## Architecture

```
Input Text → Preprocessing → Aspect Extraction → Sentiment Analysis → Result Aggregation
                    ↓                  ↓                    ↓                    ↓
             [Tokenization]    [NER/Extraction]    [Sentiment Models]   [Score Calculation]
             [Normalization]   [Aspect Mapping]    [Polarity Detection]  [Confidence Score]
```

### 기술 스택
- **Framework**: FastAPI
- **ML Models**: 
  - BERT/KoBERT (Aspect Extraction)
  - KoELECTRA (Sentiment Classification)
  - Custom Fine-tuned Models
- **NLP Libraries**: transformers, spaCy, KoNLPy
- **Database**: PostgreSQL
- **Vector DB**: pgvector

## API Endpoints

### Aspect Extraction
```http
POST /aspects/extract
```
텍스트에서 Aspect를 추출합니다.

**Request:**
```json
{
  "text": "국민연금의 수익률은 개선되었지만 가입 절차는 복잡하다",
  "domain": "pension",
  "extract_opinions": true
}
```

**Response:**
```json
{
  "aspects": [
    {
      "aspect": "수익률",
      "category": "performance",
      "start_idx": 6,
      "end_idx": 9,
      "confidence": 0.95
    },
    {
      "aspect": "가입 절차",
      "category": "accessibility",
      "start_idx": 18,
      "end_idx": 23,
      "confidence": 0.92
    }
  ],
  "opinions": [
    {
      "opinion": "개선되었다",
      "aspect_ref": "수익률",
      "polarity": "positive"
    },
    {
      "opinion": "복잡하다",
      "aspect_ref": "가입 절차",
      "polarity": "negative"
    }
  ]
}
```

### ABSA Analysis
```http
POST /analysis/absa
```
Aspect 기반 감성 분석을 수행합니다.

**Request:**
```json
{
  "text": "연금 수익률은 만족스럽지만 수수료가 너무 비싸다",
  "aspects": ["수익률", "수수료"],
  "granularity": "detailed"
}
```

**Response:**
```json
{
  "overall_sentiment": "mixed",
  "overall_score": 0.2,
  "aspect_sentiments": [
    {
      "aspect": "수익률",
      "sentiment": "positive",
      "score": 0.85,
      "confidence": 0.91,
      "supporting_text": "만족스럽지만"
    },
    {
      "aspect": "수수료",
      "sentiment": "negative",
      "score": -0.78,
      "confidence": 0.88,
      "supporting_text": "너무 비싸다"
    }
  ],
  "metadata": {
    "model_version": "absa-v2.1",
    "processing_time_ms": 234
  }
}
```

### Batch ABSA
```http
POST /analysis/batch
```
여러 문서에 대한 배치 ABSA 분석을 수행합니다.

### Aspect Categories
```http
GET /aspects/categories
```
사용 가능한 Aspect 카테고리를 조회합니다.

**Response:**
```json
{
  "categories": {
    "performance": ["수익률", "운용성과", "투자성과"],
    "stability": ["안정성", "지속가능성", "위험도"],
    "accessibility": ["가입절차", "이용편의성", "접근성"],
    "cost": ["수수료", "관리비용", "가입비용"],
    "trust": ["신뢰도", "투명성", "공정성"]
  }
}
```

### Model Management
```http
GET /models
```
사용 가능한 ABSA 모델 목록을 조회합니다.

```http
POST /models/reload
```
모델을 다시 로드합니다.

## Data Models

### Aspect
```python
class Aspect(BaseModel):
    aspect: str
    category: str
    start_idx: int
    end_idx: int
    confidence: float
    metadata: Dict[str, Any] = {}
```

### Opinion
```python
class Opinion(BaseModel):
    opinion: str
    aspect_ref: str
    polarity: Literal["positive", "neutral", "negative"]
    intensity: float
    confidence: float
```

### ABSAResult
```python
class ABSAResult(BaseModel):
    id: str
    text: str
    overall_sentiment: str
    overall_score: float
    aspect_sentiments: List[AspectSentiment]
    processing_time_ms: int
    model_version: str
    created_at: datetime
```

### AspectSentiment
```python
class AspectSentiment(BaseModel):
    aspect: str
    sentiment: str
    score: float  # -1.0 to 1.0
    confidence: float
    supporting_text: Optional[str]
    opinion_words: List[str]
```

## Dependencies

### Python Dependencies
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
transformers==4.35.0
torch==2.1.0
spacy==3.7.0
konlpy==0.6.0
python-mecab-ko==1.0.0
numpy==1.24.3
scikit-learn==1.3.2
psycopg2-binary==2.9.9
sqlalchemy==2.0.23
pydantic==2.5.0
```

### ML Models
- **Aspect Extraction**: 
  - klue/bert-base
  - Custom NER model
- **Sentiment Analysis**:
  - monologg/koelectra-base-v3-discriminator
  - Custom fine-tuned models for pension domain

### External Services
- PostgreSQL (Results storage)
- Redis (Model cache)
- ML Model Repository (S3/GCS)

## Configuration

### Environment Variables
```env
# Server
PORT=8003
DEBUG=false
LOG_LEVEL=INFO
WORKERS=2

# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/absa
POOL_SIZE=10

# Models
MODEL_PATH=/models
ASPECT_MODEL=klue-bert-aspect
SENTIMENT_MODEL=koelectra-sentiment
USE_GPU=true
MAX_SEQUENCE_LENGTH=512

# Cache
REDIS_URL=redis://redis:6379/3
MODEL_CACHE_TTL=3600

# Inference
BATCH_SIZE=16
MAX_BATCH_WAIT_MS=100
TIMEOUT_MS=5000
```

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for KoNLPy
RUN apt-get update && apt-get install -y \
    g++ openjdk-17-jdk python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Mecab
RUN apt-get update && apt-get install -y \
    mecab libmecab-dev mecab-ko-dic \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download ko_core_news_sm

# Download ML models
RUN python -c "from transformers import AutoModel, AutoTokenizer; \
    AutoModel.from_pretrained('klue/bert-base'); \
    AutoModel.from_pretrained('monologg/koelectra-base-v3-discriminator')"

COPY app/ ./app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

### GPU Deployment
```dockerfile
# Use CUDA base image for GPU support
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04
# ... rest of configuration
```

## Monitoring

### Metrics
- Aspect extraction accuracy
- Sentiment classification F1 score
- Average processing time per request
- Model inference latency
- Cache hit ratio
- Error rate by aspect category

### Custom Metrics
```python
from prometheus_client import Counter, Histogram, Summary

absa_requests = Counter(
    'absa_requests_total',
    'Total ABSA analysis requests',
    ['model', 'status']
)

aspect_extraction_time = Histogram(
    'aspect_extraction_seconds',
    'Time to extract aspects',
    ['model']
)

sentiment_accuracy = Summary(
    'sentiment_accuracy',
    'Sentiment prediction accuracy',
    ['aspect_category']
)
```

### Health Check
```python
@app.get("/health")
async def health_check():
    checks = {
        "database": await check_database(),
        "models_loaded": check_models_loaded(),
        "gpu_available": torch.cuda.is_available(),
        "memory_usage": get_memory_usage()
    }
    
    status = "healthy" if all(checks.values()[:2]) else "unhealthy"
    return {"status": status, "checks": checks}
```

## Testing

### Unit Tests
```bash
# Run all tests
pytest tests/ -v

# Test aspect extraction
pytest tests/test_aspect_extraction.py -v

# Test sentiment analysis
pytest tests/test_sentiment_analysis.py -v
```

### Performance Tests
```python
# tests/test_performance.py
def test_absa_latency():
    text = "연금 관련 긴 텍스트..."
    start = time.time()
    result = analyze_absa(text)
    latency = time.time() - start
    assert latency < 1.0  # Should complete within 1 second
```

### Model Evaluation
```python
# Evaluate aspect extraction
python scripts/evaluate_aspect_model.py --test-data data/test.json

# Evaluate sentiment classification
python scripts/evaluate_sentiment_model.py --test-data data/test.json
```

## Troubleshooting

### Common Issues

1. **Model Loading OOM**
   - Error: `RuntimeError: CUDA out of memory`
   - Solution: Reduce batch size, use model quantization

2. **Aspect Not Detected**
   - Symptom: Known aspects not extracted
   - Solution: Fine-tune model on domain data, adjust threshold

3. **Slow Inference**
   - Symptom: High latency (>2s)
   - Solution: Enable batching, use GPU, implement caching

4. **Incorrect Sentiment**
   - Symptom: Wrong polarity for aspects
   - Solution: Retrain with more domain examples

5. **Mecab Error**
   - Error: `MeCab not found`
   - Solution: Install mecab-ko-dic, set MECAB_PATH

### Debug Mode
```python
# Enable verbose logging
if settings.DEBUG:
    logger.setLevel(logging.DEBUG)
    
    # Save intermediate results
    SAVE_INTERMEDIATE = True
    
    # Enable model interpretation
    EXPLAIN_PREDICTIONS = True
```

### Performance Optimization
```python
# Batching configuration
BATCHING_CONFIG = {
    "enable_dynamic_batching": True,
    "max_batch_size": 32,
    "batch_timeout_ms": 100
}

# Model optimization
OPTIMIZATION_CONFIG = {
    "use_mixed_precision": True,
    "enable_torch_compile": True,
    "quantization": "int8"
}
```

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
