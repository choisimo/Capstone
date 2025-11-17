---
docsync: true
last_synced: 2025-09-30T09:16:00+0900
source_sha: d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3
coverage: 1.0
title: OSINT Services Detailed PRD
version: 2.0
status: draft
---
# OSINT Services 상세 PRD

## 문서 정보
- **서비스명**: OSINT Services (Orchestrator, Planning, Source)
- **버전**: 2.0
- **포트**: 8005 (Orchestrator), 8006 (Planning), 8007 (Source)
- **저장소**: `/BACKEND-OSINT-*-SERVICE`
- **소유팀**: OSINT Team
- **상태**: 초기 구현 단계 (Draft)

## 서비스 개요

### 목적
**오픈소스 인텔리전스(OSINT)** 작업을 관리하고 실행하는 서비스 그룹으로, 데이터 수집 계획, 작업 오케스트레이션, 소스 관리를 담당합니다.

### 서비스 구성
1. **OSINT Orchestrator (8005)**: 작업 큐 관리 및 워커 조정
2. **OSINT Planning (8006)**: 수집 계획 수립 및 최적화
3. **OSINT Source (8007)**: 소스 관리 및 크롤러 통합

---

## 아키텍처

### 서비스 간 관계
```
OSINT Planning → OSINT Orchestrator → OSINT Source → Web/API
      ↓                 ↓                    ↓
   계획 생성         작업 큐 관리         실제 수집
```

### 데이터 플로우
```
1. Planning: 수집 계획 생성
2. Orchestrator: 작업을 큐에 등록, 우선순위 관리
3. Source: 실제 크롤링 실행
4. Collector: 결과 검증 및 저장
```

---

## 1. OSINT Orchestrator Service (Port 8005)

### 목적
우선순위 기반 작업 큐 관리 및 워커 조정

### 핵심 기능
- 작업 큐 관리 (우선순위 기반)
- 워커 상태 모니터링
- 작업 재시도 및 실패 처리
- 작업 통계 및 메트릭

### 주요 API (계획)

#### POST `/api/v1/tasks`
작업 등록

**Request**:
```json
{
  "task_type": "crawl",
  "priority": "high",
  "payload": {
    "source_id": 1,
    "url": "https://www.nps.or.kr/...",
    "depth": 2
  }
}
```

#### GET `/api/v1/tasks`
작업 목록 조회

#### GET `/api/v1/tasks/{task_id}`
작업 상태 조회

**Response**:
```json
{
  "task_id": "task-789",
  "status": "running",
  "priority": "high",
  "worker_id": "worker-3",
  "started_at": "2025-09-30T09:10:00+09:00"
}
```

#### GET `/api/v1/workers`
워커 목록 조회

#### GET `/api/v1/metrics`
오케스트레이터 메트릭

**Response (Current)**:
```json
{
  "service": "osint-task-orchestrator",
  "queue_stats": {
    "total_tasks": 0,
    "pending_tasks": 0
  },
  "active_workers": 0,
  "total_workers": 0
}
```

---

## 2. OSINT Planning Service (Port 8006)

### 목적
효율적인 데이터 수집 계획 수립

### 핵심 기능
- 수집 계획 생성
- 소스 우선순위 결정
- 수집 일정 최적화
- 계획 템플릿 관리

### 주요 API (계획)

#### POST `/api/v1/plans`
수집 계획 생성

**Request**:
```json
{
  "name": "국민연금 주간 수집",
  "target": "nps.or.kr",
  "frequency": "weekly",
  "priority": "medium",
  "sources": [1, 2, 3],
  "parameters": {
    "depth": 2,
    "respect_robots": true
  }
}
```

#### GET `/api/v1/plans`
계획 목록 조회

#### GET `/api/v1/plans/{plan_id}`
계획 상세 조회

#### POST `/api/v1/plans/{plan_id}/execute`
계획 실행

**Response**:
```json
{
  "plan_id": 123,
  "execution_id": "exec-456",
  "status": "scheduled",
  "estimated_tasks": 25,
  "scheduled_at": "2025-09-30T10:00:00+09:00"
}
```

#### GET `/api/v1/plans/templates`
계획 템플릿 조회

---

## 3. OSINT Source Service (Port 8007)

### 목적
소스 관리 및 크롤러 통합 (Integrated Crawler Manager)

### 핵심 기능
- 데이터 소스 등록 및 관리
- 크롤러 통합 (직접 구현, changedetection.io, ScrapeGraphAI)
- URL 검증 및 Mock 데이터 감지
- 크롤링 결과 집계

### 주요 API (계획)

#### POST `/api/v1/sources`
소스 등록

**Request**:
```json
{
  "name": "국민연금공단 공지사항",
  "url": "https://www.nps.or.kr/...",
  "source_type": "web",
  "crawler_type": "direct",
  "config": {
    "selector": "div.notice-list",
    "pagination": true
  }
}
```

**Crawler Types**:
- `direct`: 직접 구현 크롤러 (40%)
- `changedetection`: changedetection.io (30%)
- `scrapegraph`: ScrapeGraphAI (20%)
- `ai`: Gemini/Perplexity (10%)

#### GET `/api/v1/sources`
소스 목록 조회

#### POST `/api/v1/sources/{source_id}/crawl`
즉시 크롤링 실행

**Response**:
```json
{
  "source_id": 1,
  "crawl_id": "crawl-789",
  "status": "running",
  "crawler_type": "direct",
  "started_at": "2025-09-30T09:16:00+09:00"
}
```

#### GET `/api/v1/sources/{source_id}/results`
크롤링 결과 조회

---

## 환경 변수

### Orchestrator
```bash
PORT=8005
DATABASE_URL=postgresql://user:pass@postgres:5432/osint_orchestrator
REDIS_URL=redis://redis:6379
MAX_WORKERS=10
QUEUE_SIZE=1000
```

### Planning
```bash
PORT=8006
DATABASE_URL=postgresql://user:pass@postgres:5432/osint_planning
PLANNING_ALGORITHM=priority_based
```

### Source
```bash
PORT=8007
DATABASE_URL=postgresql://user:pass@postgres:5432/osint_source
COLLECTOR_SERVICE_URL=http://collector-service:8002

# Crawler 설정
CRAWLER_USER_AGENT=Mozilla/5.0 (compatible; OSINTBot/1.0)
CRAWLER_TIMEOUT=30
MAX_CONCURRENT_REQUESTS=10

# 검증
URL_VALIDATION_ENABLED=true
MOCK_DETECTION_ENABLED=true
```

---

## 데이터 검증 (Source Service)

### Mock 데이터 감지
```python
mock_patterns = [
  'mock', 'fake', 'test', 'dummy', 'sample',
  'example.com', 'test.com', 'localhost',
  'random', 'placeholder'
]
```

### URL 검증
- 금지된 스키마 차단: `javascript:`, `data:`
- 허용된 도메인만 크롤링
- SSL 인증서 검증

---

## 성능 목표

| 서비스 | 메트릭 | 목표 |
|--------|--------|------|
| Orchestrator | 작업 등록 | ≤ 50ms |
| Orchestrator | 큐 조회 | ≤ 100ms |
| Planning | 계획 생성 | ≤ 2s |
| Source | 크롤링 속도 | 100 pages/min |

---

## 현재 상태

### 완료
- Orchestrator 기본 구조
- Health/Metrics 엔드포인트
- Planning 기본 구조
- Source Mock 감지 로직

### 진행 중
- 작업 큐 로직 구현
- 워커 관리 시스템
- 계획 실행 엔진
- 크롤러 통합 완성

### 계획
- 작업 재시도 로직
- 계획 템플릿 시스템
- 크롤링 결과 분석
- 성능 최적화

---

## 관련 문서
- [Collector Service PRD](collector-service-detailed-prd.md)
- [Crawler Implementation Guide](../../.windsurf/workflows/crawler-implementation-guide.md)

---

**작성일**: 2025-09-30
**작성자**: Platform Team
**리뷰 상태**: Draft
**노트**: OSINT 서비스는 현재 초기 구현 단계이며, 주요 기능은 Collector Service에서 처리 중
