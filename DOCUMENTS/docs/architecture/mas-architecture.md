# Microservice Architecture (MAS) - 연금 감성 분석 시스템

## 시스템 개요

연금 감성 분석 시스템은 마이크로서비스 아키텍처(MAS)를 기반으로 구축되어 있으며, 각 서비스는 독립적으로 배포 및 확장 가능합니다.

## 시스템 아키텍처 다이어그램

### 1. 전체 시스템 구성도

```mermaid
graph TB
    subgraph "Frontend Layer"
        FE[Frontend Dashboard<br/>:3000]
    end
    
    subgraph "API Gateway Layer"
        GW[API Gateway<br/>:8000]
    end
    
    subgraph "Microservice Layer"
        ANALYSIS[Analysis Service<br/>:8001]
        COLLECTOR[Collector Service<br/>:8002]
        ABSA[ABSA Service<br/>:8003]
        ALERT[Alert Service<br/>:8004]
    end
    
    subgraph "Worker Layer"
        WEBCOL[Web Collector Worker]
        WEBCRAWL[Web Crawler Worker]
        NEWSWATCH[News Watcher Worker]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL<br/>+ pgvector)]
        REDIS[(Redis Cache)]
        MQ[Message Queue]
    end
    
    subgraph "External Services"
        NEWS[News APIs]
        WEB[Web Sources]
        ML[ML Models]
    end
    
    FE --> GW
    GW --> ANALYSIS
    GW --> COLLECTOR
    GW --> ABSA
    GW --> ALERT
    
    COLLECTOR --> WEBCOL
    COLLECTOR --> WEBCRAWL
    COLLECTOR --> NEWSWATCH
    
    ANALYSIS --> PG
    COLLECTOR --> PG
    ABSA --> PG
    ALERT --> PG
    
    ANALYSIS --> REDIS
    COLLECTOR --> REDIS
    
    WEBCOL --> NEWS
    WEBCRAWL --> WEB
    NEWSWATCH --> NEWS
    
    ABSA --> ML
    ANALYSIS --> ML
    
    COLLECTOR --> MQ
    ANALYSIS --> MQ
    ALERT --> MQ
    
    style FE fill:#e1f5fe
    style GW fill:#fff3e0
    style ANALYSIS fill:#f3e5f5
    style COLLECTOR fill:#f3e5f5
    style ABSA fill:#f3e5f5
    style ALERT fill:#f3e5f5
    style PG fill:#e8f5e9
    style REDIS fill:#e8f5e9
    style MQ fill:#e8f5e9
```

### 2. 데이터 플로우 다이어그램

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Gateway
    participant Collector
    participant Analysis
    participant ABSA
    participant Alert
    participant DB
    
    User->>Frontend: 데이터 요청
    Frontend->>Gateway: API 호출
    Gateway->>Collector: 데이터 수집 요청
    
    Note over Collector: 웹 크롤링/RSS 수집
    Collector->>DB: 원시 데이터 저장
    Collector-->>Gateway: 수집 완료
    
    Gateway->>Analysis: 분석 요청
    Analysis->>DB: 데이터 조회
    Analysis->>Analysis: 감성 분석 수행
    Analysis->>DB: 분석 결과 저장
    
    Analysis->>ABSA: 세부 분석 요청
    ABSA->>ABSA: Aspect 추출
    ABSA->>DB: Aspect 기반 결과 저장
    ABSA-->>Analysis: 분석 완료
    
    Analysis-->>Gateway: 분석 결과
    
    Analysis->>Alert: 임계값 체크
    Alert->>Alert: 알림 규칙 확인
    Alert-->>User: 알림 전송 (필요시)
    
    Gateway-->>Frontend: 응답 데이터
    Frontend-->>User: 결과 표시
```

### 3. 서비스 간 통신 매트릭스

```mermaid
graph LR
    subgraph "Service Communication Matrix"
        GATEWAY[API Gateway]
        ANALYSIS[Analysis Service]
        COLLECTOR[Collector Service]
        ABSA[ABSA Service]
        ALERT[Alert Service]
    end
    
    GATEWAY -->|HTTP REST| ANALYSIS
    GATEWAY -->|HTTP REST| COLLECTOR
    GATEWAY -->|HTTP REST| ABSA
    GATEWAY -->|HTTP REST| ALERT
    
    COLLECTOR -->|Event/MQ| ANALYSIS
    ANALYSIS -->|Event/MQ| ABSA
    ANALYSIS -->|Event/MQ| ALERT
    ABSA -->|Event/MQ| ALERT
    
    style GATEWAY fill:#ffd54f
    style ANALYSIS fill:#ce93d8
    style COLLECTOR fill:#90caf9
    style ABSA fill:#a5d6a7
    style ALERT fill:#ef9a9a
```

## 서비스별 상세 구성

### API Gateway (포트: 8080)
- **역할**: 모든 마이크로서비스에 대한 단일 진입점
- **기능**:
  - 라우팅 및 로드 밸런싱
  - 인증 및 권한 관리
  - Rate limiting
  - 서비스 헬스 체크
- **엔드포인트**:
  - `/api/v1/analysis/*` → Analysis Service
  - `/api/v1/collector/*` → Collector Service
  - `/api/v1/absa/*` → ABSA Service
  - `/api/v1/alerts/*` → Alert Service

### Analysis Service (포트: 8001)
- **역할**: 감성 분석 및 트렌드 분석
- **기능**:
  - 감성 점수 계산
  - 트렌드 분석
  - 리포트 생성
  - ML 모델 관리
- **라우터**:
  - `/sentiment` - 감성 분석
  - `/trends` - 트렌드 분석
  - `/reports` - 리포트 생성
  - `/models` - ML 모델 관리

### Collector Service (포트: 8002)
- **역할**: 데이터 수집 및 관리
- **기능**:
  - 웹 크롤링
  - RSS 피드 수집
  - 뉴스 API 연동
  - 데이터 전처리
- **라우터**:
  - `/sources` - 데이터 소스 관리
  - `/collections` - 수집 작업 관리
  - `/feeds` - RSS 피드 관리

### ABSA Service (포트: 8003)
- **역할**: Aspect 기반 감성 분석
- **기능**:
  - Aspect 추출
  - Aspect별 감성 분석
  - 세부 분석 리포트
- **라우터**:
  - `/aspects` - Aspect 추출
  - `/analysis` - ABSA 분석
  - `/models` - ABSA 모델 관리

### Alert Service (포트: 8004)
- **역할**: 알림 및 경고 시스템
- **기능**:
  - 알림 규칙 관리
  - 실시간 알림 전송
  - 알림 히스토리 관리
- **라우터**:
  - `/alerts` - 알림 관리
  - `/rules` - 알림 규칙
  - `/notifications` - 알림 전송

## 트랜잭션 관리

### 1. 분산 트랜잭션 패턴

```mermaid
graph LR
    subgraph "Saga Pattern Implementation"
        START[트랜잭션 시작]
        COLLECT[데이터 수집<br/>Collector Service]
        ANALYZE[데이터 분석<br/>Analysis Service]
        ABSA_PROC[ABSA 처리<br/>ABSA Service]
        ALERT_CHECK[알림 체크<br/>Alert Service]
        COMMIT[커밋]
        ROLLBACK[롤백]
    end
    
    START --> COLLECT
    COLLECT -->|성공| ANALYZE
    COLLECT -->|실패| ROLLBACK
    ANALYZE -->|성공| ABSA_PROC
    ANALYZE -->|실패| ROLLBACK
    ABSA_PROC -->|성공| ALERT_CHECK
    ABSA_PROC -->|실패| ROLLBACK
    ALERT_CHECK -->|성공| COMMIT
    ALERT_CHECK -->|실패| ROLLBACK
    
    style START fill:#81c784
    style COMMIT fill:#4fc3f7
    style ROLLBACK fill:#e57373
```

### 2. 이벤트 소싱 패턴

```mermaid
graph TB
    subgraph "Event Store"
        ES[(Event Store)]
    end
    
    subgraph "Services"
        SVC1[Service A]
        SVC2[Service B]
        SVC3[Service C]
    end
    
    subgraph "Event Types"
        E1[Data Collected]
        E2[Analysis Complete]
        E3[Alert Triggered]
    end
    
    SVC1 -->|Publish| E1
    SVC2 -->|Publish| E2
    SVC3 -->|Publish| E3
    
    E1 --> ES
    E2 --> ES
    E3 --> ES
    
    ES -->|Subscribe| SVC1
    ES -->|Subscribe| SVC2
    ES -->|Subscribe| SVC3
```

## 배포 아키텍처

### Docker Compose 구성

```mermaid
graph TB
    subgraph "Docker Network"
        subgraph "Application Services"
            FE_CONT[frontend:3000]
            GW_CONT[api-gateway:8000]
            ANA_CONT[analysis:8001]
            COL_CONT[collector:8002]
            ABSA_CONT[absa:8003]
            ALERT_CONT[alert:8004]
        end
        
        subgraph "Infrastructure Services"
            PG_CONT[postgres:5432]
            REDIS_CONT[redis:6379]
            RABBIT_CONT[rabbitmq:5672]
        end
    end
    
    FE_CONT --> GW_CONT
    GW_CONT --> ANA_CONT
    GW_CONT --> COL_CONT
    GW_CONT --> ABSA_CONT
    GW_CONT --> ALERT_CONT
    
    ANA_CONT --> PG_CONT
    COL_CONT --> PG_CONT
    ABSA_CONT --> PG_CONT
    ALERT_CONT --> PG_CONT
    
    ANA_CONT --> REDIS_CONT
    COL_CONT --> REDIS_CONT
    
    COL_CONT --> RABBIT_CONT
    ANA_CONT --> RABBIT_CONT
    ALERT_CONT --> RABBIT_CONT
```

## 확장성 및 성능 최적화

### 1. 수평 확장 전략

- **API Gateway**: 로드 밸런서 뒤에 다중 인스턴스 배치
- **Analysis Service**: CPU 집약적 작업을 위한 오토스케일링
- **Collector Service**: 동시 수집 작업을 위한 워커 풀
- **ABSA Service**: GPU 기반 ML 처리를 위한 전용 노드
- **Alert Service**: 실시간 처리를 위한 인메모리 캐싱

### 2. 캐싱 전략

```mermaid
graph LR
    subgraph "Cache Layers"
        L1[Browser Cache]
        L2[CDN Cache]
        L3[API Gateway Cache]
        L4[Service Cache]
        L5[Database Cache]
    end
    
    L1 --> L2
    L2 --> L3
    L3 --> L4
    L4 --> L5
    
    style L1 fill:#ffecb3
    style L2 fill:#ffe0b2
    style L3 fill:#ffd54f
    style L4 fill:#ffca28
    style L5 fill:#ffb300
```

## 모니터링 및 로깅

### 1. 모니터링 스택

- **Prometheus**: 메트릭 수집
- **Grafana**: 시각화 대시보드
- **ELK Stack**: 로그 수집 및 분석
- **Jaeger**: 분산 트레이싱

### 2. 헬스 체크 엔드포인트

모든 서비스는 `/health` 엔드포인트를 제공하며, 다음 정보를 반환합니다:
- 서비스 상태
- 데이터베이스 연결 상태
- 의존 서비스 상태
- 응답 시간

## 보안 고려사항

### 1. 인증 및 권한 관리

- JWT 기반 인증
- OAuth 2.0 지원
- Role-based Access Control (RBAC)
- API Key 관리

### 2. 네트워크 보안

- TLS/SSL 암호화
- VPN 터널링
- 방화벽 규칙
- DDoS 보호

## 개발 환경 설정

### 로컬 개발

```bash
# Docker Compose로 전체 시스템 실행
docker-compose -f docker-compose.msa.yml up

# 개별 서비스 실행
cd BACKEND-{SERVICE_NAME}
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app/main.py
```

### 환경 변수 설정

각 서비스는 `.env` 파일을 통해 설정됩니다:
- `DATABASE_URL`: PostgreSQL 연결 문자열
- `REDIS_URL`: Redis 연결 문자열
- `RABBITMQ_URL`: RabbitMQ 연결 문자열
- `SERVICE_PORT`: 서비스 포트
- `DEBUG`: 디버그 모드
- `LOG_LEVEL`: 로깅 레벨
