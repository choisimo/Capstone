"""
하이브리드 지능형 크롤링 시스템 메인
통합 실행 및 사용 예제
"""
import asyncio
import os
from datetime import timedelta
from typing import Dict, Any, List

# Phase 1 컴포넌트
from gemini_client_v2 import GeminiClientV2
from scrapegraph_adapter_v2 import (
    ScrapeGraphAIAdapterV2, 
    ScrapeConfig, 
    ScrapeStrategy
)
from template_learner import TemplateLearner
from change_detection_v2 import (
    ChangeDetectionServiceV2,
    MonitoringConfig,
    MonitoringStrategy
)
from change_evaluator import ChangeImportanceEvaluator

# Phase 2 컴포넌트
from orchestrator.orchestrator import CrawlingOrchestrator, TaskType, TaskPriority
from orchestrator.workflow_engine import WorkflowEngine, WorkflowBuilder
from orchestrator.scheduler import TaskScheduler
from orchestrator.event_bus import EventBus, EventType
from orchestrator.state_manager import StateManager, PersistenceMode
from orchestrator.error_handler import ErrorHandler, RetryPolicy, RetryStrategy


class HybridCrawlerSystem:
    """
    하이브리드 크롤링 시스템 통합 클래스
    
    모든 컴포넌트를 통합하여 사용하기 쉬운 인터페이스 제공
    """
    
    def __init__(self, gemini_api_key: str = None):
        """초기화"""
        # API 키 설정
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        
        # 오케스트레이터 초기화
        self.orchestrator = CrawlingOrchestrator(
            gemini_api_key=self.gemini_api_key,
            max_workers=5
        )
        
        # 추가 컴포넌트
        self.workflow_engine = WorkflowEngine()
        self.scheduler = TaskScheduler()
        self.event_bus = EventBus()
        self.state_manager = StateManager(PersistenceMode.FILE)
        self.error_handler = ErrorHandler()
        
        # 이벤트 구독 설정
        self._setup_event_subscriptions()
        
        self.is_running = False
    
    async def start(self):
        """시스템 시작"""
        if self.is_running:
            print("System already running")
            return
        
        print("🚀 Starting Hybrid Crawler System...")
        
        # 컴포넌트 시작
        await self.orchestrator.start()
        await self.scheduler.start()
        await self.event_bus.start()
        
        self.is_running = True
        print("✅ System started successfully")
    
    async def stop(self):
        """시스템 중지"""
        if not self.is_running:
            return
        
        print("🛑 Stopping Hybrid Crawler System...")
        
        # 컴포넌트 중지
        await self.orchestrator.stop()
        await self.scheduler.stop()
        await self.event_bus.stop()
        
        self.is_running = False
        print("✅ System stopped")
    
    def _setup_event_subscriptions(self):
        """이벤트 구독 설정"""
        # 작업 완료 이벤트
        async def on_task_completed(event):
            print(f"✅ Task completed: {event.data.get('task_id')}")
        
        # 변경 감지 이벤트
        async def on_change_detected(event):
            print(f"🔄 Change detected: {event.data.get('url')}")
            importance = event.data.get('importance_score', 0)
            if importance > 0.7:
                print(f"  ⚠️ High importance change! Score: {importance}")
        
        # 에러 이벤트
        async def on_error(event):
            print(f"❌ Error: {event.data.get('error')}")
        
        self.event_bus.subscribe_callback(
            on_task_completed,
            [EventType.TASK_COMPLETED]
        )
        self.event_bus.subscribe_callback(
            on_change_detected,
            [EventType.CHANGE_DETECTED]
        )
        self.event_bus.subscribe_callback(
            on_error,
            [EventType.SYSTEM_ERROR]
        )
    
    # === 간편 메서드들 ===
    
    async def scrape(
        self, 
        url: str,
        prompt: str = "",
        strategy: str = "smart"
    ) -> Dict[str, Any]:
        """
        웹페이지 스크래핑
        
        Args:
            url: 스크래핑할 URL
            prompt: 추출 지시사항
            strategy: 스크래핑 전략
        
        Returns:
            스크래핑 결과
        """
        task_id = await self.orchestrator.create_task(
            TaskType.SCRAPE,
            {
                "url": url,
                "prompt": prompt,
                "strategy": ScrapeStrategy.SMART_SCRAPER
            },
            priority=TaskPriority.HIGH
        )
        
        # 작업 완료 대기
        while True:
            status = self.orchestrator.get_task_status(task_id)
            if status and status['status'] in ['completed', 'failed']:
                return status
            await asyncio.sleep(0.5)
    
    async def monitor(
        self,
        url: str,
        keywords: List[str] = None,
        interval_hours: int = 1
    ) -> str:
        """
        웹페이지 모니터링 시작
        
        Args:
            url: 모니터링할 URL
            keywords: 추적할 키워드
            interval_hours: 체크 간격 (시간)
        
        Returns:
            모니터링 ID
        """
        return await self.orchestrator.add_monitoring_job(
            url=url,
            keywords=keywords,
            check_interval_hours=interval_hours
        )
    
    async def analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """
        감성 분석
        
        Args:
            content: 분석할 텍스트
        
        Returns:
            분석 결과
        """
        task_id = await self.orchestrator.create_task(
            TaskType.ANALYZE,
            {
                "content": content,
                "prompt_type": "sentiment"
            },
            priority=TaskPriority.MEDIUM
        )
        
        # 결과 대기
        while True:
            status = self.orchestrator.get_task_status(task_id)
            if status and status['status'] == 'completed':
                return status
            await asyncio.sleep(0.5)
    
    async def create_workflow(self, name: str) -> WorkflowBuilder:
        """
        워크플로우 생성
        
        Args:
            name: 워크플로우 이름
        
        Returns:
            워크플로우 빌더
        """
        return WorkflowBuilder(name)
    
    def schedule_daily_scraping(
        self,
        url: str,
        hour: int,
        minute: int = 0
    ) -> str:
        """
        매일 정기 스크래핑 예약
        
        Args:
            url: 스크래핑할 URL
            hour: 실행 시간 (시)
            minute: 실행 시간 (분)
        
        Returns:
            스케줄 ID
        """
        async def scrape_job():
            await self.scrape(url)
        
        return self.scheduler.schedule_daily(
            f"Daily scraping: {url}",
            scrape_job,
            hour,
            minute
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """시스템 통계"""
        return {
            "orchestrator": self.orchestrator.get_statistics(),
            "scheduler": self.scheduler.get_statistics(),
            "event_bus": self.event_bus.get_statistics(),
            "state_manager": self.state_manager.get_statistics(),
            "error_handler": self.error_handler.get_statistics()
        }


# === 사용 예제 ===

async def example_basic_usage():
    """기본 사용 예제"""
    # 시스템 초기화
    system = HybridCrawlerSystem()
    await system.start()
    
    try:
        # 1. 단순 스크래핑
        print("\n📋 Scraping example...")
        result = await system.scrape(
            url="https://www.nps.or.kr",
            prompt="국민연금 관련 주요 뉴스를 추출해주세요"
        )
        print(f"Scraping result: {result}")
        
        # 2. 감성 분석
        print("\n🎭 Sentiment analysis example...")
        sentiment = await system.analyze_sentiment(
            "국민연금 보험료 인상은 불가피한 선택입니다."
        )
        print(f"Sentiment: {sentiment}")
        
        # 3. 모니터링 시작
        print("\n👁️ Starting monitoring...")
        monitor_id = await system.monitor(
            url="https://www.nps.or.kr/news",
            keywords=["연금개혁", "보험료", "수급"],
            interval_hours=1
        )
        print(f"Monitoring started with ID: {monitor_id}")
        
        # 4. 통계 확인
        print("\n📊 System statistics:")
        stats = system.get_statistics()
        print(stats)
        
    finally:
        await system.stop()


async def example_workflow():
    """워크플로우 사용 예제"""
    system = HybridCrawlerSystem()
    await system.start()
    
    try:
        # 워크플로우 정의
        builder = await system.create_workflow("연금 뉴스 분석")
        
        # 스텝 추가
        scrape_step = builder.add_action(
            "뉴스 스크래핑",
            lambda ctx: system.scrape(ctx['url'])
        )
        
        analyze_step = builder.add_action(
            "감성 분석",
            lambda ctx: system.analyze_sentiment(ctx['content'])
        )
        
        # 스텝 연결
        builder.connect(scrape_step, analyze_step)
        
        # 워크플로우 빌드 및 실행
        workflow = builder.build()
        
        result = await system.workflow_engine.execute_workflow(
            workflow,
            initial_context={
                "url": "https://www.nps.or.kr/news/latest"
            }
        )
        
        print(f"Workflow result: {result}")
        
    finally:
        await system.stop()


async def example_scheduled_monitoring():
    """스케줄된 모니터링 예제"""
    system = HybridCrawlerSystem()
    await system.start()
    
    try:
        # 매일 오전 9시 스크래핑
        schedule_id = system.schedule_daily_scraping(
            url="https://www.nps.or.kr",
            hour=9,
            minute=0
        )
        print(f"Scheduled daily scraping: {schedule_id}")
        
        # 30초 동안 실행
        await asyncio.sleep(30)
        
    finally:
        await system.stop()


async def main():
    """메인 함수"""
    print("=" * 60)
    print("하이브리드 지능형 크롤링 시스템")
    print("=" * 60)
    
    # 기본 사용 예제
    await example_basic_usage()
    
    # 워크플로우 예제
    # await example_workflow()
    
    # 스케줄 예제
    # await example_scheduled_monitoring()


if __name__ == "__main__":
    # 환경변수 설정 확인
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️ Warning: GEMINI_API_KEY not set in environment variables")
        print("Please set: export GEMINI_API_KEY='your-api-key'")
    
    # 실행
    asyncio.run(main())
