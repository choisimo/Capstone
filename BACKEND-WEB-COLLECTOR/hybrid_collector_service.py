"""
Enhanced Collector Service with Hybrid AI Approach

This service integrates:
- Gemini AI for pension sentiment analysis
- ScrapeGraphAI adapter for intelligent web scraping
- Original ChangeDetection.io functionality
- Advanced orchestration and strategy selection
"""

from __future__ import annotations

import asyncio
import os
import json
import time
import logging
from typing import List, Optional, Tuple, Any, Dict, Union
from dataclasses import dataclass, asdict
from enum import Enum

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, HttpUrl
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse

# Support running as script or as package
try:
    from .config import ChangeDetectionConfig, AgentConfig, PerplexityConfig, BusConfig
    from .cdio_client import ChangeDetectionClient
    from .perplexity_client import PerplexityClient
    from .gemini_client import GeminiClient, GeminiModel
    from .scrapegraph_adapter import (
        ScrapeGraphAIAdapter, ScrapeRequest, ScrapeStrategy,
        create_smart_scraper, create_search_scraper
    )
except Exception:
    import sys
    sys.path.append(os.path.dirname(__file__))
    from config import ChangeDetectionConfig, AgentConfig, PerplexityConfig, BusConfig
    from cdio_client import ChangeDetectionClient
    from perplexity_client import PerplexityClient
    from gemini_client import GeminiClient, GeminiModel
    from scrapegraph_adapter import (
        ScrapeGraphAIAdapter, ScrapeRequest, ScrapeStrategy,
        create_smart_scraper, create_search_scraper
    )


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CollectionStrategy(Enum):
    """Collection strategies for different scenarios"""
    TRADITIONAL = "traditional"  # Original ChangeDetection.io only
    AI_ENHANCED = "ai_enhanced"  # ChangeDetection.io + AI analysis
    SMART_SCRAPING = "smart_scraping"  # ScrapeGraphAI + Gemini analysis
    HYBRID = "hybrid"  # Intelligent strategy selection


class ContentType(Enum):
    """Content type classification"""
    NEWS_ARTICLE = "news_article"
    GOVERNMENT_POLICY = "government_policy" 
    FORUM_DISCUSSION = "forum_discussion"
    ACADEMIC_PAPER = "academic_paper"
    SOCIAL_MEDIA = "social_media"
    UNKNOWN = "unknown"


@dataclass
class GeminiConfig:
    """Gemini AI configuration"""
    api_key: str
    model: str = GeminiModel.FLASH_15.value
    timeout: int = 30
    
    @staticmethod
    def from_env() -> "GeminiConfig":
        """Load configuration from environment variables"""
        api_key = os.getenv("GEMINI_API_KEY", "")
        model = os.getenv("GEMINI_MODEL", GeminiModel.FLASH_15.value)
        timeout = int(os.getenv("GEMINI_TIMEOUT", "30"))
        return GeminiConfig(api_key=api_key, model=model, timeout=timeout)


@dataclass
class HybridConfig:
    """Hybrid collection configuration"""
    enable_ai: bool = True
    enable_smart_scraping: bool = True
    strategy_selection: str = "auto"  # auto, manual
    ai_confidence_threshold: float = 0.7
    fallback_strategy: CollectionStrategy = CollectionStrategy.TRADITIONAL
    
    @staticmethod
    def from_env() -> "HybridConfig":
        """Load configuration from environment variables"""
        return HybridConfig(
            enable_ai=os.getenv("ENABLE_AI", "1") in ("1", "true", "True"),
            enable_smart_scraping=os.getenv("ENABLE_SMART_SCRAPING", "1") in ("1", "true", "True"),
            strategy_selection=os.getenv("STRATEGY_SELECTION", "auto"),
            ai_confidence_threshold=float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.7")),
            fallback_strategy=CollectionStrategy(os.getenv("FALLBACK_STRATEGY", "traditional"))
        )


# Enhanced request models
class EnhancedGenerateStepsRequest(BaseModel):
    url: HttpUrl
    instruction: str = Field(..., description="Natural language instructions")
    strategy: Optional[CollectionStrategy] = None
    use_ai: bool = True
    content_type: Optional[ContentType] = None


class EnhancedCreateWatchRequest(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    instruction: Optional[str] = None
    strategy: Optional[CollectionStrategy] = None
    use_ai: bool = True
    content_type: Optional[ContentType] = None
    pension_focus: bool = True
    tags: Optional[List[str]] = None
    notification_urls: Optional[List[str]] = None
    recheck: Optional[bool] = None


class AIAnalysisRequest(BaseModel):
    """Request for AI-powered content analysis"""
    url: HttpUrl
    content: Optional[str] = None
    strategy: ScrapeStrategy = ScrapeStrategy.SMART_SCRAPER
    pension_focus: bool = True


class AIAnalysisResponse(BaseModel):
    """Response from AI analysis"""
    success: bool
    analysis: Dict[str, Any]
    strategy_used: str
    execution_time: float
    confidence: float
    recommendations: List[str]
    error: Optional[str] = None


class StrategyRecommendationRequest(BaseModel):
    """Request for strategy recommendation"""
    url: HttpUrl
    content_hints: Optional[List[str]] = None
    historical_data: Optional[Dict[str, Any]] = None


class StrategyRecommendationResponse(BaseModel):
    """Strategy recommendation response"""
    recommended_strategy: CollectionStrategy
    confidence: float
    reasoning: str
    alternative_strategies: List[Dict[str, Any]]


class HybridCollectorService:
    """
    Enhanced collector service with hybrid AI capabilities
    """
    
    def __init__(self):
        """Initialize the hybrid collector service"""
        # Load configurations
        self.cd_config = ChangeDetectionConfig.from_env()
        self.agent_config = AgentConfig.from_env()
        self.pplx_config = PerplexityConfig.from_env()
        self.gemini_config = GeminiConfig.from_env()
        self.hybrid_config = HybridConfig.from_env()
        self.bus_config = BusConfig.from_env()
        
        # Initialize clients
        self.cd_client = ChangeDetectionClient(self.cd_config.base_url, self.cd_config.api_key)
        
        # Initialize AI clients if configured
        self.gemini_client = None
        self.scrapegraph_adapter = None
        self.pplx_client = None
        
        if self.gemini_config.api_key and self.hybrid_config.enable_ai:
            self.gemini_client = GeminiClient(
                api_key=self.gemini_config.api_key,
                model=self.gemini_config.model,
                timeout=self.gemini_config.timeout
            )
            
            if self.hybrid_config.enable_smart_scraping:
                self.scrapegraph_adapter = ScrapeGraphAIAdapter(
                    gemini_api_key=self.gemini_config.api_key,
                    gemini_model=self.gemini_config.model,
                    enable_logging=True
                )
        
        if self.pplx_config.api_key:
            self.pplx_client = PerplexityClient(
                self.pplx_config.base_url,
                self.pplx_config.api_key,
                model=self.pplx_config.model,
                timeout=self.pplx_config.timeout_sec
            )
        
        logger.info("Hybrid Collector Service initialized")
        logger.info(f"AI enabled: {self.hybrid_config.enable_ai}")
        logger.info(f"Smart scraping enabled: {self.hybrid_config.enable_smart_scraping}")
        logger.info(f"Gemini configured: {self.gemini_client is not None}")
        logger.info(f"ScrapeGraphAI configured: {self.scrapegraph_adapter is not None}")

    async def analyze_url_content(self, url: str, content: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze URL content using AI to determine best collection strategy
        
        Args:
            url: Target URL
            content: Optional pre-fetched content
            
        Returns:
            Analysis results with strategy recommendations
        """
        if not self.gemini_client:
            return {
                "content_type": ContentType.UNKNOWN.value,
                "recommended_strategy": CollectionStrategy.TRADITIONAL.value,
                "confidence": 0.0,
                "reasoning": "AI not configured"
            }
        
        try:
            # If content not provided, fetch it using ScrapeGraphAI
            if not content and self.scrapegraph_adapter:
                request = ScrapeRequest(
                    url=url,
                    prompt="Extract main content and classify the content type",
                    strategy=ScrapeStrategy.SMART_SCRAPER
                )
                result = self.scrapegraph_adapter.scrape(request)
                if result.success:
                    content = result.data.get("extracted_content", "")
            
            # Fallback: basic content fetch
            if not content:
                import requests
                try:
                    response = requests.get(url, timeout=10)
                    content = response.text[:5000]  # Limit content
                except Exception:
                    content = ""
            
            # Analyze with Gemini
            analysis = self.gemini_client.analyze_pension_content(content, url)
            
            # Determine content type and strategy
            content_type = self._classify_content_type(url, content, analysis)
            strategy = self._recommend_strategy(content_type, analysis)
            
            return {
                "content_type": content_type.value,
                "recommended_strategy": strategy.value,
                "confidence": analysis.get("confidence", 0.0),
                "reasoning": self._generate_strategy_reasoning(content_type, strategy, analysis),
                "pension_relevance": analysis.get("relevance_score", 0.0),
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Content analysis failed for {url}: {str(e)}")
            return {
                "content_type": ContentType.UNKNOWN.value,
                "recommended_strategy": CollectionStrategy.TRADITIONAL.value,
                "confidence": 0.0,
                "reasoning": f"Analysis failed: {str(e)}",
                "error": str(e)
            }

    def _classify_content_type(self, url: str, content: str, analysis: Dict[str, Any]) -> ContentType:
        """Classify content type based on URL and analysis"""
        url_lower = url.lower()
        
        # Government sites
        if any(domain in url_lower for domain in ["gov.kr", "moel.go.kr", "nps.or.kr"]):
            return ContentType.GOVERNMENT_POLICY
        
        # News sites
        if any(domain in url_lower for domain in ["news", "newsis", "yonhap", "chosun", "joongang"]):
            return ContentType.NEWS_ARTICLE
        
        # Academic/research
        if any(domain in url_lower for domain in ["ac.kr", "edu", "kdi.re.kr", "kli.re.kr"]):
            return ContentType.ACADEMIC_PAPER
        
        # Forum/community
        if any(keyword in url_lower for keyword in ["forum", "cafe", "community", "board"]):
            return ContentType.FORUM_DISCUSSION
        
        # Social media
        if any(domain in url_lower for domain in ["facebook", "twitter", "instagram", "blog"]):
            return ContentType.SOCIAL_MEDIA
        
        # Use AI analysis for further classification
        key_topics = analysis.get("key_topics", [])
        if any("정책" in topic or "법안" in topic for topic in key_topics):
            return ContentType.GOVERNMENT_POLICY
        elif any("뉴스" in topic or "기사" in topic for topic in key_topics):
            return ContentType.NEWS_ARTICLE
        
        return ContentType.UNKNOWN

    def _recommend_strategy(self, content_type: ContentType, analysis: Dict[str, Any]) -> CollectionStrategy:
        """Recommend collection strategy based on content type and analysis"""
        if not self.hybrid_config.enable_ai:
            return CollectionStrategy.TRADITIONAL
        
        confidence = analysis.get("confidence", 0.0)
        relevance = analysis.get("relevance_score", 0.0)
        
        # High-value content gets smart scraping
        if (confidence > self.hybrid_config.ai_confidence_threshold and 
            relevance > 0.8 and 
            self.hybrid_config.enable_smart_scraping):
            return CollectionStrategy.SMART_SCRAPING
        
        # Government/academic content gets AI enhancement
        if content_type in [ContentType.GOVERNMENT_POLICY, ContentType.ACADEMIC_PAPER]:
            return CollectionStrategy.AI_ENHANCED
        
        # News articles get hybrid approach
        if content_type == ContentType.NEWS_ARTICLE and relevance > 0.5:
            return CollectionStrategy.HYBRID
        
        # Default to AI enhanced if AI is available
        if self.gemini_client:
            return CollectionStrategy.AI_ENHANCED
        
        return CollectionStrategy.TRADITIONAL

    def _generate_strategy_reasoning(self, content_type: ContentType, strategy: CollectionStrategy, analysis: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for strategy selection"""
        reasoning_parts = []
        
        # Content type reasoning
        content_reasons = {
            ContentType.GOVERNMENT_POLICY: "정부 정책 문서로 정확한 분석이 필요",
            ContentType.NEWS_ARTICLE: "뉴스 기사로 실시간 모니터링이 중요",
            ContentType.ACADEMIC_PAPER: "학술 논문으로 정밀한 분석이 필요",
            ContentType.FORUM_DISCUSSION: "포럼 토론으로 여론 분석이 중요",
            ContentType.SOCIAL_MEDIA: "소셜 미디어로 트렌드 분석이 필요"
        }
        
        if content_type in content_reasons:
            reasoning_parts.append(content_reasons[content_type])
        
        # Relevance reasoning
        relevance = analysis.get("relevance_score", 0.0)
        if relevance > 0.8:
            reasoning_parts.append("연금 관련성이 매우 높음")
        elif relevance > 0.5:
            reasoning_parts.append("연금 관련성이 중간 수준")
        else:
            reasoning_parts.append("연금 관련성이 낮음")
        
        # Strategy reasoning
        strategy_reasons = {
            CollectionStrategy.SMART_SCRAPING: "AI 기반 지능형 수집으로 최고 품질 분석",
            CollectionStrategy.AI_ENHANCED: "AI 향상된 분석으로 고품질 데이터 추출",
            CollectionStrategy.HYBRID: "하이브리드 접근으로 균형잡힌 수집",
            CollectionStrategy.TRADITIONAL: "전통적 수집 방식으로 안정적 모니터링"
        }
        
        if strategy in strategy_reasons:
            reasoning_parts.append(strategy_reasons[strategy])
        
        return "; ".join(reasoning_parts)

    async def smart_scrape_content(self, url: str, prompt: str, strategy: ScrapeStrategy) -> Dict[str, Any]:
        """
        Perform smart scraping using ScrapeGraphAI adapter
        
        Args:
            url: Target URL
            prompt: Scraping instruction
            strategy: Scraping strategy
            
        Returns:
            Scraping results
        """
        if not self.scrapegraph_adapter:
            raise HTTPException(status_code=503, detail="Smart scraping not configured")
        
        try:
            request = ScrapeRequest(
                url=url,
                prompt=prompt,
                strategy=strategy,
                timeout=30
            )
            
            result = self.scrapegraph_adapter.scrape(request)
            
            return {
                "success": result.success,
                "data": result.data,
                "metadata": result.metadata,
                "execution_time": result.execution_time,
                "tokens_used": result.tokens_used,
                "error": result.error
            }
            
        except Exception as e:
            logger.error(f"Smart scraping failed for {url}: {str(e)}")
            return {
                "success": False,
                "data": {},
                "metadata": {"error": str(e)},
                "execution_time": 0.0,
                "tokens_used": 0,
                "error": f"Smart scraping failed: {str(e)}"
            }

    async def generate_search_queries(self, topic: str, count: int = 5) -> List[str]:
        """Generate optimized search queries for a topic"""
        if not self.gemini_client:
            # Fallback queries
            return [
                f"{topic} 국민연금",
                f"{topic} 연금 정책",
                f"{topic} pension Korea",
                f"Korea pension {topic}",
                f"{topic} 기초연금"
            ][:count]
        
        try:
            queries = self.gemini_client.generate_search_queries(topic, count)
            return queries
        except Exception as e:
            logger.error(f"Query generation failed: {str(e)}")
            # Return fallback queries
            return [f"{topic} 연금", f"{topic} pension"][:count]


# Global service instance
collector_service = HybridCollectorService()

# FastAPI application
app = FastAPI(
    title="Hybrid AI Collector Service",
    version="2.0.0",
    description="Enhanced web collector with AI-powered analysis and smart scraping"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <h2>Hybrid AI Collector Service v2.0</h2>
    <p>Enhanced web collector with:</p>
    <ul>
        <li>Gemini AI integration</li>
        <li>ScrapeGraphAI adapter</li>
        <li>Intelligent strategy selection</li>
        <li>Pension sentiment analysis</li>
    </ul>
    <p>See <a href="/docs">/docs</a> for API documentation</p>
    """


@app.get("/api/v2/health")
def health_check():
    """Enhanced health check with service status"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "services": {
            "changedetection": bool(collector_service.cd_client),
            "gemini_ai": collector_service.gemini_client is not None,
            "smart_scraping": collector_service.scrapegraph_adapter is not None,
            "perplexity": collector_service.pplx_client is not None
        },
        "configuration": {
            "ai_enabled": collector_service.hybrid_config.enable_ai,
            "smart_scraping_enabled": collector_service.hybrid_config.enable_smart_scraping,
            "strategy_selection": collector_service.hybrid_config.strategy_selection
        }
    }


@app.post("/api/v2/analyze", response_model=AIAnalysisResponse)
async def analyze_content(request: AIAnalysisRequest):
    """
    Analyze web content using AI
    
    This endpoint provides comprehensive AI-powered analysis of web content,
    including pension sentiment analysis and content classification.
    """
    start_time = time.time()
    
    try:
        if request.strategy == ScrapeStrategy.SMART_SCRAPER:
            # Use smart scraping for content extraction and analysis
            result = await collector_service.smart_scrape_content(
                url=str(request.url),
                prompt="Extract and analyze pension-related content with sentiment analysis",
                strategy=request.strategy
            )
            
            if not result["success"]:
                raise HTTPException(status_code=400, detail=result["error"])
            
            analysis = result["data"]
            execution_time = result["execution_time"]
            
        elif collector_service.gemini_client:
            # Direct Gemini analysis
            content = request.content or ""
            if not content:
                # Fetch content first
                import requests
                try:
                    response = requests.get(str(request.url), timeout=10)
                    content = response.text
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Failed to fetch content: {str(e)}")
            
            analysis = collector_service.gemini_client.analyze_pension_content(
                content=content,
                url=str(request.url)
            )
            execution_time = time.time() - start_time
        
        else:
            raise HTTPException(status_code=503, detail="AI analysis not configured")
        
        # Generate recommendations
        recommendations = []
        confidence = analysis.get("confidence", 0.0)
        relevance = analysis.get("relevance_score", 0.0)
        
        if confidence > 0.8:
            recommendations.append("High confidence analysis - suitable for automated processing")
        if relevance > 0.8:
            recommendations.append("High pension relevance - priority for monitoring")
        if analysis.get("policy_impact") == "high":
            recommendations.append("High policy impact - alert stakeholders")
        
        return AIAnalysisResponse(
            success=True,
            analysis=analysis,
            strategy_used=request.strategy.value,
            execution_time=execution_time,
            confidence=confidence,
            recommendations=recommendations
        )
        
    except Exception as e:
        logger.error(f"Content analysis failed: {str(e)}")
        return AIAnalysisResponse(
            success=False,
            analysis={},
            strategy_used=request.strategy.value,
            execution_time=time.time() - start_time,
            confidence=0.0,
            recommendations=[],
            error=str(e)
        )


@app.post("/api/v2/recommend-strategy", response_model=StrategyRecommendationResponse)
async def recommend_strategy(request: StrategyRecommendationRequest):
    """
    Recommend optimal collection strategy for a URL
    
    Analyzes the target URL and recommends the best collection strategy
    based on content type, relevance, and historical performance.
    """
    try:
        analysis = await collector_service.analyze_url_content(str(request.url))
        
        recommended_strategy = CollectionStrategy(analysis["recommended_strategy"])
        confidence = analysis["confidence"]
        reasoning = analysis["reasoning"]
        
        # Generate alternative strategies
        alternatives = []
        for strategy in CollectionStrategy:
            if strategy != recommended_strategy:
                alt_confidence = confidence * 0.8 if strategy == CollectionStrategy.AI_ENHANCED else confidence * 0.6
                alternatives.append({
                    "strategy": strategy.value,
                    "confidence": alt_confidence,
                    "pros": f"Alternative approach using {strategy.value}",
                    "cons": f"Lower confidence than {recommended_strategy.value}"
                })
        
        return StrategyRecommendationResponse(
            recommended_strategy=recommended_strategy,
            confidence=confidence,
            reasoning=reasoning,
            alternative_strategies=alternatives
        )
        
    except Exception as e:
        logger.error(f"Strategy recommendation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Strategy recommendation failed: {str(e)}")


@app.post("/api/v2/generate-queries")
async def generate_queries(
    topic: str = Query(..., description="Topic for query generation"),
    count: int = Query(5, ge=1, le=20, description="Number of queries to generate")
):
    """
    Generate optimized search queries for a topic
    
    Uses AI to generate diverse, effective search queries for pension-related topics.
    """
    try:
        queries = await collector_service.generate_search_queries(topic, count)
        return {
            "topic": topic,
            "queries": queries,
            "count": len(queries),
            "generated_at": time.time()
        }
    except Exception as e:
        logger.error(f"Query generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query generation failed: {str(e)}")


# Enhanced watch creation with AI integration
@app.post("/api/v2/create-watch")
async def create_enhanced_watch(request: EnhancedCreateWatchRequest):
    """
    Create enhanced watch with AI-powered strategy selection
    
    This endpoint creates a monitoring watch with intelligent strategy selection
    and AI-powered analysis configuration.
    """
    try:
        # Analyze URL to determine optimal strategy
        if request.strategy is None and request.use_ai:
            analysis = await collector_service.analyze_url_content(str(request.url))
            strategy = CollectionStrategy(analysis["recommended_strategy"])
            logger.info(f"AI recommended strategy: {strategy.value} for {request.url}")
        else:
            strategy = request.strategy or CollectionStrategy.TRADITIONAL
        
        # Create watch payload based on strategy
        payload = {
            "url": str(request.url),
            "fetch_backend": "html_webdriver",
        }
        
        if request.title:
            payload["title"] = request.title
        if request.tags:
            payload["tags"] = request.tags
        if request.notification_urls:
            payload["notification_urls"] = request.notification_urls
        
        # Add AI-specific metadata
        if request.use_ai:
            payload["ai_strategy"] = strategy.value
            payload["pension_focus"] = request.pension_focus
            payload["content_type"] = request.content_type.value if request.content_type else None
        
        # Create the watch
        result = collector_service.cd_client.create_watch(payload)
        
        return {
            "result": result,
            "strategy_used": strategy.value,
            "ai_enabled": request.use_ai,
            "pension_focus": request.pension_focus
        }
        
    except Exception as e:
        logger.error(f"Enhanced watch creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Watch creation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    cfg = AgentConfig.from_env()
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=cfg.port, 
        reload=os.getenv("UVICORN_RELOAD", "0") in ("1", "true", "True")
    )