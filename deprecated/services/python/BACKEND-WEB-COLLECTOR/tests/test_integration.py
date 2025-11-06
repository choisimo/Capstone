"""
통합 테스트
전체 시스템 통합 테스트
"""
import pytest
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any

# 시스템 임포트
from hybrid_crawler_main import HybridCrawlerSystem
from api.main import create_app
from database.database import init_db, close_db
from cache.cache_manager import init_cache, close_cache
from messaging.kafka_client import init_message_queue, close_message_queue


@pytest.fixture
async def system():
    """시스템 픽스처"""
    system = HybridCrawlerSystem()
    await system.initialize()
    yield system
    await system.shutdown()


@pytest.fixture
async def api_client():
    """API 클라이언트 픽스처"""
    app = create_app()
    
    # 테스트 클라이언트 생성
    from httpx import AsyncClient
    from fastapi.testclient import TestClient
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def database():
    """데이터베이스 픽스처"""
    db = init_db(
        database_url="sqlite:///test.db",
        create_tables=True,
        echo=False
    )
    yield db
    close_db()


@pytest.fixture
async def cache():
    """캐시 픽스처"""
    cache = init_cache(cache_type="memory")
    yield cache
    await close_cache()


@pytest.fixture
async def message_queue():
    """메시지 큐 픽스처"""
    mq = init_message_queue()
    if mq:
        await mq.start()
    yield mq
    if mq:
        await close_message_queue()


class TestSystemIntegration:
    """시스템 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_system_initialization(self, system):
        """시스템 초기화 테스트"""
        assert system is not None
        assert system.orchestrator is not None
        assert system.scraper is not None
        assert system.detector is not None
        assert system.workflow_engine is not None
        assert system.scheduler is not None
        assert system.event_bus is not None
        assert system.state_manager is not None
    
    @pytest.mark.asyncio
    async def test_scraping_workflow(self, system):
        """스크래핑 워크플로우 테스트"""
        # 스크래핑 요청
        url = "https://example.com"
        result = await system.scrape_url(
            url=url,
            strategy="smart",
            prompt="Extract main content"
        )
        
        assert result is not None
        assert "data" in result
        assert result.get("success", False)
    
    @pytest.mark.asyncio
    async def test_analysis_workflow(self, system):
        """분석 워크플로우 테스트"""
        content = "이것은 테스트 콘텐츠입니다. 매우 긍정적인 내용입니다."
        
        # 감성 분석
        result = await system.analyze_content(
            content=content,
            analysis_types=["sentiment"]
        )
        
        assert result is not None
        assert "sentiment" in result
        assert "score" in result["sentiment"]
    
    @pytest.mark.asyncio
    async def test_monitoring_workflow(self, system):
        """모니터링 워크플로우 테스트"""
        # 모니터링 시작
        monitoring_id = await system.start_monitoring(
            url="https://example.com",
            check_interval=60,
            keywords=["test", "example"]
        )
        
        assert monitoring_id is not None
        
        # 모니터링 상태 확인
        status = await system.get_monitoring_status(monitoring_id)
        assert status is not None
        assert status.get("is_active", False)
        
        # 모니터링 중지
        stopped = await system.stop_monitoring(monitoring_id)
        assert stopped
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self, system):
        """워크플로우 실행 테스트"""
        # 워크플로우 정의
        workflow = {
            "name": "test_workflow",
            "steps": [
                {
                    "id": "scrape",
                    "type": "action",
                    "action": "scrape",
                    "params": {
                        "url": "https://example.com",
                        "strategy": "smart"
                    }
                },
                {
                    "id": "analyze",
                    "type": "action",
                    "action": "analyze",
                    "params": {
                        "analysis_type": "sentiment",
                        "use_previous": "scrape.content"
                    }
                }
            ]
        }
        
        # 워크플로우 실행
        result = await system.execute_workflow(workflow)
        
        assert result is not None
        assert result.get("status") == "completed"
        assert "results" in result
    
    @pytest.mark.asyncio
    async def test_event_bus(self, system):
        """이벤트 버스 테스트"""
        received_events = []
        
        # 이벤트 핸들러 등록
        def handler(event):
            received_events.append(event)
        
        system.event_bus.subscribe("test.event", handler)
        
        # 이벤트 발행
        await system.event_bus.publish("test.event", {"data": "test"})
        
        # 약간의 대기
        await asyncio.sleep(0.1)
        
        assert len(received_events) > 0
        assert received_events[0]["data"] == "test"


class TestAPIIntegration:
    """API 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, api_client):
        """헬스 체크 엔드포인트 테스트"""
        response = await api_client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert "components" in data
    
    @pytest.mark.asyncio
    async def test_scrape_endpoint(self, api_client):
        """스크래핑 엔드포인트 테스트"""
        payload = {
            "url": "https://example.com",
            "strategy": "smart",
            "prompt": "Extract content"
        }
        
        response = await api_client.post("/api/v1/crawler/scrape", json=payload)
        assert response.status_code in [200, 202]
        
        data = response.json()
        if response.status_code == 202:
            # 비동기 처리
            assert "task_id" in data
        else:
            # 동기 처리
            assert "data" in data
    
    @pytest.mark.asyncio
    async def test_analysis_endpoint(self, api_client):
        """분석 엔드포인트 테스트"""
        payload = {
            "content": "테스트 콘텐츠입니다.",
            "analysis_type": "sentiment",
            "language": "ko"
        }
        
        response = await api_client.post("/api/v1/analysis/analyze", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "result" in data
    
    @pytest.mark.asyncio
    async def test_monitoring_crud(self, api_client):
        """모니터링 CRUD 테스트"""
        # 생성
        payload = {
            "url": "https://example.com",
            "check_interval": 60,
            "keywords": ["test"]
        }
        
        response = await api_client.post("/api/v1/monitoring/start", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        monitoring_id = data["monitoring_id"]
        
        # 조회
        response = await api_client.get(f"/api/v1/monitoring/{monitoring_id}")
        assert response.status_code == 200
        
        # 목록 조회
        response = await api_client.get("/api/v1/monitoring/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
        # 중지
        response = await api_client.post(f"/api/v1/monitoring/{monitoring_id}/stop")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_workflow_endpoint(self, api_client):
        """워크플로우 엔드포인트 테스트"""
        workflow = {
            "name": "api_test_workflow",
            "steps": [
                {
                    "id": "step1",
                    "type": "action",
                    "action": "print",
                    "params": {"message": "test"}
                }
            ]
        }
        
        response = await api_client.post("/api/v1/workflow/execute", json=workflow)
        assert response.status_code in [200, 202]
    
    @pytest.mark.asyncio
    async def test_metrics_endpoint(self, api_client):
        """메트릭 엔드포인트 테스트"""
        response = await api_client.get("/metrics")
        assert response.status_code == 200
        
        # Prometheus 형식 체크
        assert response.headers.get("content-type") == "text/plain; version=0.0.4"


class TestDatabaseIntegration:
    """데이터베이스 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_task_crud(self, database):
        """작업 CRUD 테스트"""
        from database.repositories import TaskRepository
        
        with database.session_scope() as session:
            repo = TaskRepository(session)
            
            # 생성
            task = repo.create(
                task_type="scraping",
                status="pending",
                priority="high",
                config={"url": "https://example.com"}
            )
            
            assert task.id is not None
            assert task.task_type == "scraping"
            
            # 조회
            fetched = repo.get(task.id)
            assert fetched is not None
            assert fetched.id == task.id
            
            # 업데이트
            updated = repo.update_status(
                task.id,
                "completed",
                result={"success": True}
            )
            assert updated.status == "completed"
            
            # 목록 조회
            tasks = repo.get_by_status("completed")
            assert len(tasks) > 0
    
    @pytest.mark.asyncio
    async def test_scrape_result_storage(self, database):
        """스크래핑 결과 저장 테스트"""
        from database.repositories import ScrapeRepository
        
        with database.session_scope() as session:
            repo = ScrapeRepository(session)
            
            # 저장
            result = repo.create(
                task_id="test-task-id",
                url="https://example.com",
                strategy="smart",
                success=True,
                data={"content": "test content"},
                execution_time=1.5
            )
            
            assert result.id is not None
            
            # 조회
            results = repo.get_by_url("https://example.com")
            assert len(results) > 0
            assert results[0].url == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_monitoring_config(self, database):
        """모니터링 설정 테스트"""
        from database.repositories import MonitoringRepository
        
        with database.session_scope() as session:
            repo = MonitoringRepository(session)
            
            # 생성
            config = repo.create(
                url="https://example.com",
                strategy="content",
                keywords=["test", "example"],
                check_interval_minutes=60
            )
            
            assert config.id is not None
            
            # 활성 모니터링 조회
            active = repo.get_active()
            assert len(active) > 0
            
            # 체크 대상 조회
            due = repo.get_due_for_check()
            assert isinstance(due, list)
            
            # 비활성화
            deactivated = repo.deactivate(config.id)
            assert deactivated


class TestCacheIntegration:
    """캐시 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_cache_operations(self, cache):
        """캐시 기본 작업 테스트"""
        # 설정
        key = "test:key"
        value = {"data": "test value"}
        
        success = await cache.set(key, value, ttl=60)
        assert success
        
        # 조회
        cached = await cache.get(key)
        assert cached is not None
        assert cached["data"] == "test value"
        
        # 존재 확인
        exists = await cache.exists(key)
        assert exists
        
        # 삭제
        deleted = await cache.delete(key)
        assert deleted
        
        # 삭제 후 확인
        exists = await cache.exists(key)
        assert not exists
    
    @pytest.mark.asyncio
    async def test_cache_decorator(self, cache):
        """캐시 데코레이터 테스트"""
        from cache.decorators import cache_result
        
        call_count = 0
        
        @cache_result(ttl=60, prefix="test")
        async def expensive_function(value: int):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # 비싼 연산 시뮬레이션
            return value * 2
        
        # 첫 번째 호출
        result1 = await expensive_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # 두 번째 호출 (캐시됨)
        result2 = await expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # 호출 횟수가 증가하지 않음
        
        # 다른 인자로 호출
        result3 = await expensive_function(10)
        assert result3 == 20
        assert call_count == 2


class TestMessageQueueIntegration:
    """메시지 큐 통합 테스트"""
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not message_queue, reason="Kafka not available")
    async def test_message_publish_subscribe(self, message_queue):
        """메시지 발행/구독 테스트"""
        from messaging.message_models import TaskMessage, MessageType
        
        received = []
        
        # 핸들러
        async def handler(message):
            received.append(message)
        
        # 구독
        consumer = await message_queue.subscribe(
            topics=["test.topic"],
            group_id="test-group",
            handler=handler
        )
        
        # 메시지 발행
        message = TaskMessage(
            type=MessageType.TASK_CREATED,
            source="test",
            task_id="test-task",
            task_type="test",
            status="pending"
        )
        
        success = await message_queue.publish(
            message,
            topic="test.topic"
        )
        assert success
        
        # 메시지 수신 대기
        await asyncio.sleep(1)
        
        assert len(received) > 0
        
        # 구독 해제
        await message_queue.unsubscribe(f"test-group:test.topic")


class TestEndToEndScenarios:
    """엔드-투-엔드 시나리오 테스트"""
    
    @pytest.mark.asyncio
    async def test_news_monitoring_scenario(self, system):
        """뉴스 모니터링 시나리오"""
        # 1. 뉴스 사이트 모니터링 시작
        monitoring_id = await system.start_monitoring(
            url="https://news.example.com",
            check_interval=300,  # 5분
            keywords=["국민연금", "연금개혁"],
            ai_analysis=True
        )
        
        assert monitoring_id is not None
        
        # 2. 초기 스크래핑
        initial_content = await system.scrape_url(
            url="https://news.example.com",
            strategy="smart",
            prompt="뉴스 기사 추출"
        )
        
        assert initial_content is not None
        
        # 3. 감성 분석
        if initial_content.get("data", {}).get("content"):
            analysis = await system.analyze_content(
                content=initial_content["data"]["content"],
                analysis_types=["sentiment", "keywords", "summary"]
            )
            
            assert "sentiment" in analysis
            assert "keywords" in analysis
            assert "summary" in analysis
        
        # 4. 모니터링 중지
        stopped = await system.stop_monitoring(monitoring_id)
        assert stopped
    
    @pytest.mark.asyncio
    async def test_batch_processing_scenario(self, system):
        """배치 처리 시나리오"""
        urls = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com"
        ]
        
        # 워크플로우 정의
        workflow = {
            "name": "batch_scraping",
            "steps": []
        }
        
        # 각 URL에 대한 스텝 추가
        for i, url in enumerate(urls):
            workflow["steps"].append({
                "id": f"scrape_{i}",
                "type": "action",
                "action": "scrape",
                "params": {
                    "url": url,
                    "strategy": "fast"
                }
            })
        
        # 병렬 처리 스텝
        workflow["steps"].append({
            "id": "parallel_analysis",
            "type": "parallel",
            "steps": [
                {
                    "id": f"analyze_{i}",
                    "type": "action",
                    "action": "analyze",
                    "params": {
                        "use_previous": f"scrape_{i}.content",
                        "analysis_type": "sentiment"
                    }
                }
                for i in range(len(urls))
            ]
        })
        
        # 워크플로우 실행
        result = await system.execute_workflow(workflow)
        
        assert result is not None
        assert result.get("status") == "completed"
        
        # 결과 확인
        if "results" in result:
            for i in range(len(urls)):
                assert f"scrape_{i}" in result["results"]
                assert f"analyze_{i}" in result["results"]


# 실행을 위한 메인 함수
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
