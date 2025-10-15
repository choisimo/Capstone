---
docsync: true
last_synced: 2025-10-15T20:03:08+0900
source_sha: f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0
coverage: 1.0
title: API Gateway Detailed PRD
version: 2.0
status: approved
---
# API Gateway 상세 PRD

## 📋 문서 정보
- **서비스명**: Pension Sentiment Analysis API Gateway
- **버전**: 2.0
- **포트**: 8000
- **저장소**: `/BACKEND-API-GATEWAY`
- **소유팀**: Platform Team

## 🎯 서비스 개요

### 목적
모든 마이크로서비스에 대한 **단일 진입점(Single Entry Point)** 역할을 하며, 요청 라우팅, 서비스 헬스 체크, CORS 처리를 담당합니다.

### 핵심 기능
1. **요청 라우팅**: 클라이언트 요청을 적절한 마이크로서비스로 프록시
2. **헬스 체크**: 모든 서비스의 상태 모니터링
3. **CORS 처리**: 프론트엔드 크로스 오리진 요청 허용
4. **에러 처리**: 서비스 타임아웃 및 연결 오류 통합 처리
5. **로드 밸런싱**: (향후) 서비스 인스턴스 간 부하 분산

---

## 🏗️ 아키텍처

### 라우팅 구조
```
API Gateway (Port 8000)
├── /api/v1/analysis     → Analysis Service (8001)
├── /api/v1/collector    → Collector Service (8002)
├── /api/v1/absa         → ABSA Service (8003)
├── /api/v1/alerts       → Alert Service (8004)
├── /api/v1/osint-orchestrator → OSINT Orchestrator (8005)
├── /api/v1/osint-planning     → OSINT Planning (8006)
└── /api/v1/osint-source       → OSINT Source (8007)
```

### Reverse Proxy 패턴
```
Client → API Gateway → httpx.AsyncClient → Microservice
          ↓
    - 타임아웃: 30초
    - 재시도: 없음 (서비스 책임)
    - 에러 처리: 504/503
```

---

## 🔌 API 명세

### Core Endpoints

#### GET `/`
API Gateway 정보

**Response**:
```json
{
  "message": "Pension Sentiment Analysis API Gateway",
  "version": "1.0.0",
  "services": {
    "analysis": "/api/v1/analysis",
    "collector": "/api/v1/collector",
    "absa": "/api/v1/absa",
    "alerts": "/api/v1/alerts",
    "osint-orchestrator": "/api/v1/osint-orchestrator",
    "osint-planning": "/api/v1/osint-planning",
    "osint-source": "/api/v1/osint-source"
  },
  "docs": "/docs",
  "health": "/health"
}
```

#### GET `/health`
전체 시스템 헬스 체크

**Response (Healthy)**:
```json
{
  "status": "healthy",
  "services": {
    "analysis": {
      "status": "healthy",
      "response_time": 0.025
    },
    "collector": {
      "status": "healthy",
      "response_time": 0.032
    },
    "absa": {
      "status": "healthy",
      "response_time": 0.028
    },
    "alert": {
      "status": "healthy",
      "response_time": 0.019
    },
    "osint-orchestrator": {
      "status": "healthy",
      "response_time": 0.045
    },
    "osint-planning": {
      "status": "healthy",
      "response_time": 0.038
    },
    "osint-source": {
      "status": "healthy",
      "response_time": 0.041
    }
  },
  "gateway_version": "1.0.0"
}
```

**Response (Degraded)**:
```json
{
  "status": "degraded",
  "services": {
    "analysis": {
      "status": "healthy",
      "response_time": 0.025
    },
    "collector": {
      "status": "unhealthy",
      "error": "Connection refused"
    }
  },
  "gateway_version": "1.0.0"
}
```

---

### Proxied Service Endpoints

모든 서비스 엔드포인트는 API Gateway를 통해 프록시됩니다.

#### Analysis Service
- `POST /api/v1/analysis/sentiment/analyze`
- `GET /api/v1/analysis/trends/popular`
- `POST /api/v1/analysis/reports/generate`

#### Collector Service
- `POST /api/v1/collector/sources/`
- `GET /api/v1/collector/collections/`
- `POST /api/v1/collector/feeds/{feed_id}/fetch`

#### ABSA Service
- `POST /api/v1/absa/aspects/extract`
- `POST /api/v1/absa/analysis/analyze`
- `GET /api/v1/absa/personas/{user}/analyze`

##### Routing Notes
- ABSA personas endpoints are mounted in the backend under `/api/v1/personas/*`. The gateway rewrites `/api/v1/absa/personas/*` → `api/v1/personas/*` when proxying to the ABSA service.

#### Alert Service
- `POST /api/v1/alerts/rules/`
- `GET /api/v1/alerts/notifications/`
- `POST /api/v1/alerts/rules/{rule_id}/test`

#### OSINT Services
- `POST /api/v1/osint-orchestrator/plans/execute`
- `GET /api/v1/osint-planning/plans/`
- `POST /api/v1/osint-source/sources/`

---

## ⚙️ 환경 변수

```bash
# 서비스
PORT=8000
DEBUG=false
LOG_LEVEL=INFO

# Microservices URLs
ANALYSIS_SERVICE_URL=http://analysis-service:8001
COLLECTOR_SERVICE_URL=http://collector-service:8002
ABSA_SERVICE_URL=http://absa-service:8003
ALERT_SERVICE_URL=http://alert-service:8004
OSINT_ORCHESTRATOR_SERVICE_URL=http://osint-orchestrator:8005
OSINT_PLANNING_SERVICE_URL=http://osint-planning:8006
OSINT_SOURCE_SERVICE_URL=http://osint-source:8007

# Timeouts
REQUEST_TIMEOUT=30
HEALTH_CHECK_TIMEOUT=5

# CORS
CORS_ORIGINS=["*"]
```

---

## 🔒 보안

### CORS 설정
```python
allow_origins=["*"]          # 프로덕션: 특정 도메인만
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

### 향후 추가 예정
- **JWT 인증**: API Gateway 레벨 토큰 검증
- **Rate Limiting**: IP/사용자별 요청 제한
- **API Key**: 외부 API 접근 제어

---

## 📈 성능 목표

| 메트릭 | 목표 |
|--------|------|
| 프록시 오버헤드 | ≤ 10ms |
| 헬스 체크 응답 | ≤ 100ms |
| 동시 연결 | 1000+ |
| 처리량 | 500 req/s |

---

## 🔄 에러 처리

### Timeout (504 Gateway Timeout)
```json
{
  "detail": "Service timeout - please try again later"
}
```

**발생 조건**: 서비스 응답 > 30초

### Connection Error (503 Service Unavailable)
```json
{
  "detail": "Service temporarily unavailable"
}
```

**발생 조건**: 서비스 연결 실패

---

## 🧪 테스트 전략

### 수용 기준
- ✅ 모든 서비스 라우팅 정상 작동
- ✅ 헬스 체크 정확성
- ✅ 타임아웃 처리 검증
- ✅ CORS 헤더 확인

---

## 📋 관련 문서
- [Analysis Service PRD](analysis-service-detailed-prd.md)
- [ABSA Service PRD](absa-service-detailed-prd.md)
- [Collector Service PRD](collector-service-detailed-prd.md)

---

**작성일**: 2025-09-30  
**작성자**: Platform Team  
**리뷰 상태**: Approved
