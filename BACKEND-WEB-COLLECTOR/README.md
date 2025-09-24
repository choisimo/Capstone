# 🚀 Hybrid Intelligent Crawling System

## 개요

하이브리드 지능형 크롤링 시스템은 AI 기반 웹 스크래핑, 구조 학습, 변경 감지를 통합한 차세대 크롤링 솔루션입니다.

## 🌟 주요 특징

### Phase 1: Foundation (완료)
- **Gemini AI 통합**: 강력한 AI 분석 능력
- **도메인 특화 프롬프트**: 연금 도메인 최적화
- **구조화된 파싱**: 다양한 응답 형식 지원
- **ScrapeGraphAI 스타일 워크플로우**: 그래프 기반 스크래핑
- **AI 구조 학습**: 자동 템플릿 생성 및 최적화
- **지능형 변경 감지**: AI 기반 중요도 평가
- **변경 중요도 평가**: 다각도 분석 및 알림 우선순위

### Phase 2: Orchestration (완료)
- **통합 오케스트레이터**: 중앙 작업 관리
- **워크플로우 엔진**: 복잡한 작업 시퀀스
- **스케줄러**: Cron 및 다양한 스케줄 지원
- **이벤트 버스**: 비동기 이벤트 기반 통신
- **상태 관리**: 다양한 저장소 지원
- **에러 처리**: 서킷 브레이커 & 재시도 전략

## 📦 설치

### 1. 의존성 설치

```bash
pip install -r requirements_hybrid.txt
```

### 2. 환경 변수 설정

```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

또는 `.env` 파일 생성:

```
GEMINI_API_KEY=your-gemini-api-key
```

## 🎯 빠른 시작

### 기본 사용법

```python
import asyncio
from hybrid_crawler_main import HybridCrawlerSystem

async def main():
    # 시스템 초기화
    system = HybridCrawlerSystem()
    await system.start()
    
    try:
        # 웹페이지 스크래핑
        result = await system.scrape(
            url="https://www.example.com",
            prompt="주요 뉴스를 추출해주세요"
        )
        print(result)
        
        # 감성 분석
        sentiment = await system.analyze_sentiment(
            "이 텍스트의 감성을 분석합니다."
        )
        print(sentiment)
        
        # 웹페이지 모니터링
        monitor_id = await system.monitor(
            url="https://www.example.com",
            keywords=["중요", "변경"],
            interval_hours=1
        )
        print(f"Monitoring ID: {monitor_id}")
        
    finally:
        await system.stop()

asyncio.run(main())
```

### 워크플로우 사용

```python
async def workflow_example():
    system = HybridCrawlerSystem()
    await system.start()
    
    # 워크플로우 생성
    builder = await system.create_workflow("뉴스 분석 워크플로우")
    
    # 스텝 추가
    scrape_id = builder.add_action(
        "스크래핑",
        lambda ctx: system.scrape(ctx['url'])
    )
    
    analyze_id = builder.add_action(
        "분석",
        lambda ctx: system.analyze_sentiment(ctx['content'])
    )
    
    # 스텝 연결
    builder.connect(scrape_id, analyze_id)
    
    # 실행
    workflow = builder.build()
    result = await system.workflow_engine.execute_workflow(
        workflow,
        {"url": "https://example.com"}
    )
```

### 스케줄링

```python
# 매일 오전 9시에 스크래핑
schedule_id = system.schedule_daily_scraping(
    url="https://www.example.com",
    hour=9,
    minute=0
)
```

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────┐
│          Orchestration Layer            │
│  ┌──────────┐ ┌──────────┐ ┌────────┐  │
│  │Scheduler │ │Workflow  │ │Event   │  │
│  │          │ │Engine    │ │Bus     │  │
│  └──────────┘ └──────────┘ └────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌────────┐  │
│  │State     │ │Error     │ │Task    │  │
│  │Manager   │ │Handler   │ │Queue   │  │
│  └──────────┘ └──────────┘ └────────┘  │
└─────────────────────────────────────────┘
                    │
┌─────────────────────────────────────────┐
│           Foundation Layer              │
│  ┌──────────┐ ┌──────────┐ ┌────────┐  │
│  │Gemini    │ │Scraper   │ │Template│  │
│  │Client    │ │Adapter   │ │Learner │  │
│  └──────────┘ └──────────┘ └────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌────────┐  │
│  │Change    │ │Prompt    │ │Parser  │  │
│  │Detector  │ │Templates │ │System  │  │
│  └──────────┘ └──────────┘ └────────┘  │
└─────────────────────────────────────────┘
```

## 📂 프로젝트 구조

```
BACKEND-WEB-COLLECTOR/
├── orchestrator/           # Phase 2: 오케스트레이션
│   ├── orchestrator.py     # 메인 오케스트레이터
│   ├── workflow_engine.py  # 워크플로우 엔진
│   ├── scheduler.py        # 스케줄러
│   ├── event_bus.py        # 이벤트 시스템
│   ├── state_manager.py    # 상태 관리
│   └── error_handler.py    # 에러 처리
│
├── prompts/               # 프롬프트 템플릿
│   ├── base.py
│   ├── sentiment.py
│   ├── absa.py
│   ├── pension.py
│   ├── news.py
│   ├── structure.py
│   └── change.py
│
├── parsers/               # 응답 파서
│   ├── base_parser.py
│   ├── gemini_parser.py
│   ├── json_parser.py
│   └── structured_parser.py
│
├── gemini_client_v2.py    # Gemini AI 클라이언트
├── scrapegraph_adapter_v2.py  # 스크래핑 어댑터
├── template_learner.py    # 템플릿 학습
├── change_detection_v2.py # 변경 감지
├── change_evaluator.py    # 중요도 평가
└── hybrid_crawler_main.py # 메인 통합 클래스
```

## 🔧 주요 컴포넌트

### 1. Gemini AI Client
- 다양한 분석 타입 지원
- 비동기 처리
- 재시도 로직

### 2. ScrapeGraph Adapter
- 그래프 기반 워크플로우
- AI 구조 학습
- 하이브리드 전략

### 3. Template Learner
- 자동 구조 분석
- 템플릿 최적화
- 버전 관리

### 4. Change Detection
- 실시간 모니터링
- 이벤트 기반 알림
- 중요도 평가

### 5. Orchestrator
- 중앙 작업 관리
- 우선순위 큐
- 비동기 워커 풀

### 6. Workflow Engine
- 복잡한 시퀀스 실행
- 조건부/병렬 실행
- 서브 워크플로우

## 📊 모니터링

시스템 통계 조회:

```python
stats = system.get_statistics()
print(stats)
```

출력 예시:
```json
{
  "orchestrator": {
    "tasks_created": 42,
    "tasks_completed": 38,
    "tasks_failed": 2,
    "queue_size": 2
  },
  "scheduler": {
    "total_jobs": 5,
    "running_jobs": 1,
    "scheduled_jobs": 4
  },
  "event_bus": {
    "events_published": 156,
    "events_processed": 154
  }
}
```

## 🧪 테스트

```bash
# 단위 테스트
pytest tests/

# 커버리지 포함
pytest --cov=. tests/

# 특정 테스트
pytest tests/test_gemini_client_v2.py
```

## 🚀 성능 최적화

- **비동기 처리**: 모든 I/O 작업 비동기화
- **워커 풀**: 동시 작업 처리
- **캐싱**: 템플릿 및 결과 캐싱
- **재시도 전략**: 지능적 백오프
- **서킷 브레이커**: 장애 격리

## 📝 라이센스

MIT License

## 🤝 기여

기여를 환영합니다! PR을 보내주세요.

## 📮 문의

이슈를 통해 문의해주세요.
