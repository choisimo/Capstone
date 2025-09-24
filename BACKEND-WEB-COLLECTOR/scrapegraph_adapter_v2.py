"""
ScrapeGraphAI 어댑터 v2.0
개선된 AI 기반 웹 스크래핑 시스템
"""
from __future__ import annotations
import asyncio
import time
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
import hashlib
from urllib.parse import urlparse, urljoin

from gemini_client_v2 import GeminiClientV2
from parsers.gemini_parser import GeminiResponseParser
from prompts.structure import StructureLearningPromptTemplate

logger = logging.getLogger(__name__)


class ScrapeStrategy(Enum):
    """스크래핑 전략"""
    AI_LEARNING = "ai_learning"  # AI 구조 학습
    TEMPLATE_BASED = "template_based"  # 템플릿 기반
    SMART_SCRAPER = "smart_scraper"  # AI 스마트 추출
    SEARCH_SCRAPER = "search_scraper"  # 검색 결과
    STRUCTURED_SCRAPER = "structured_scraper"  # 구조화 데이터
    HYBRID = "hybrid"  # 하이브리드


class ContentType(Enum):
    """콘텐츠 타입"""
    NEWS = "news"
    BLOG = "blog"
    FORUM = "forum"
    SOCIAL = "social"
    GOVERNMENT = "government"
    RESEARCH = "research"
    UNKNOWN = "unknown"


@dataclass
class ScrapeConfig:
    """스크래핑 설정"""
    url: str
    prompt: str = ""
    strategy: ScrapeStrategy = ScrapeStrategy.SMART_SCRAPER
    target_fields: List[str] = field(default_factory=lambda: [
        "title", "content", "author", "date", "category", "tags"
    ])
    output_format: str = "json"
    max_retries: int = 3
    timeout: int = 30
    use_cache: bool = True
    follow_links: bool = False
    max_depth: int = 1
    custom_headers: Dict[str, str] = field(default_factory=dict)
    proxy: Optional[str] = None


@dataclass
class ScrapeResult:
    """스크래핑 결과"""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    error: Optional[str] = None
    execution_time: float = 0.0
    tokens_used: int = 0
    strategy_used: str = ""
    confidence_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "success": self.success,
            "data": self.data,
            "metadata": self.metadata,
            "error": self.error,
            "execution_time": self.execution_time,
            "tokens_used": self.tokens_used,
            "strategy_used": self.strategy_used,
            "confidence_score": self.confidence_score
        }


class NodeType(Enum):
    """그래프 노드 타입"""
    FETCH = "fetch"  # 웹 페이지 가져오기
    PARSE = "parse"  # HTML 파싱
    EXTRACT = "extract"  # 데이터 추출
    TRANSFORM = "transform"  # 데이터 변환
    VALIDATE = "validate"  # 검증


class GraphNode:
    """스크래핑 그래프 노드"""
    
    def __init__(self, node_type: NodeType, name: str):
        self.node_type = node_type
        self.name = name
        self.inputs: List[str] = []
        self.outputs: List[str] = []
        self.processor = None
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """노드 실행"""
        if self.processor:
            return await self.processor(context)
        return context


class ScrapingGraph:
    """스크래핑 워크플로우 그래프"""
    
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[Tuple[str, str]] = []
        self.execution_order: List[str] = []
    
    def add_node(self, node: GraphNode) -> 'ScrapingGraph':
        """노드 추가"""
        self.nodes[node.name] = node
        return self
    
    def add_edge(self, from_node: str, to_node: str) -> 'ScrapingGraph':
        """엣지 추가"""
        self.edges.append((from_node, to_node))
        return self
    
    def build(self) -> 'ScrapingGraph':
        """실행 순서 빌드"""
        # 간단한 토폴로지 정렬
        visited = set()
        order = []
        
        def dfs(node_name: str):
            if node_name in visited:
                return
            visited.add(node_name)
            for from_node, to_node in self.edges:
                if to_node == node_name and from_node not in visited:
                    dfs(from_node)
            order.append(node_name)
        
        for node_name in self.nodes:
            if node_name not in visited:
                dfs(node_name)
        
        self.execution_order = order
        return self
    
    async def execute(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """그래프 실행"""
        context = initial_context.copy()
        
        for node_name in self.execution_order:
            if node_name in self.nodes:
                node = self.nodes[node_name]
                context = await node.execute(context)
        
        return context


class ScrapeGraphAIAdapterV2:
    """
    개선된 ScrapeGraphAI 어댑터
    
    특징:
    - 그래프 기반 워크플로우
    - AI 구조 학습
    - 템플릿 캐싱
    - 하이브리드 전략
    """
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        enable_logging: bool = True
    ):
        """초기화"""
        self.gemini_client = GeminiClientV2(api_key=gemini_api_key)
        self.parser = GeminiResponseParser()
        self.structure_prompt = StructureLearningPromptTemplate()
        
        # 캐시
        self.template_cache: Dict[str, Dict[str, Any]] = {}
        self.domain_strategies: Dict[str, ScrapeStrategy] = {}
        
        # 세션
        self._session: Optional[aiohttp.ClientSession] = None
        
        if enable_logging:
            logging.basicConfig(level=logging.INFO)
        
        self.logger = logger
    
    async def __aenter__(self):
        """비동기 컨텍스트 진입"""
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 종료"""
        if self._session:
            await self._session.close()
    
    async def scrape(self, config: ScrapeConfig) -> ScrapeResult:
        """
        메인 스크래핑 메서드
        
        Args:
            config: 스크래핑 설정
        
        Returns:
            스크래핑 결과
        """
        start_time = time.time()
        
        try:
            # 전략 선택
            strategy = await self._select_strategy(config)
            self.logger.info(f"Selected strategy: {strategy.value}")
            
            # 그래프 구성
            graph = self._build_graph(strategy)
            
            # 초기 컨텍스트
            context = {
                "config": config,
                "strategy": strategy,
                "start_time": start_time
            }
            
            # 그래프 실행
            result_context = await graph.execute(context)
            
            # 결과 생성
            execution_time = time.time() - start_time
            
            return ScrapeResult(
                success=True,
                data=result_context.get("extracted_data", {}),
                metadata={
                    "url": config.url,
                    "content_type": result_context.get("content_type", "unknown"),
                    "template_used": result_context.get("template_id"),
                    "timestamp": datetime.utcnow().isoformat()
                },
                execution_time=execution_time,
                strategy_used=strategy.value,
                confidence_score=result_context.get("confidence", 0.0)
            )
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            return ScrapeResult(
                success=False,
                data={},
                metadata={"url": config.url},
                error=str(e),
                execution_time=time.time() - start_time
            )
    
    async def learn_structure(
        self, 
        url: str,
        sample_html: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        웹페이지 구조 학습
        
        Args:
            url: 학습할 URL
            sample_html: HTML 샘플 (선택적)
        
        Returns:
            학습된 구조 템플릿
        """
        if not sample_html:
            sample_html = await self._fetch_page(url)
        
        # AI 분석
        prompt = self.structure_prompt.format_prompt(
            sample_html,
            url=url,
            page_type='auto-detect'
        )
        
        response = await self.gemini_client.analyze_content(
            prompt,
            prompt_type='structure_learning'
        )
        
        if response.status == 'success':
            template = response.data
            
            # 캐시 저장
            domain = urlparse(url).netloc
            self.template_cache[domain] = template
            
            return template
        
        return {}
    
    def _build_graph(self, strategy: ScrapeStrategy) -> ScrapingGraph:
        """
        전략에 따른 그래프 구성
        
        Args:
            strategy: 스크래핑 전략
        
        Returns:
            구성된 그래프
        """
        graph = ScrapingGraph()
        
        # 공통 노드
        fetch_node = GraphNode(NodeType.FETCH, "fetch")
        fetch_node.processor = self._fetch_processor
        
        parse_node = GraphNode(NodeType.PARSE, "parse")
        parse_node.processor = self._parse_processor
        
        validate_node = GraphNode(NodeType.VALIDATE, "validate")
        validate_node.processor = self._validate_processor
        
        graph.add_node(fetch_node).add_node(parse_node).add_node(validate_node)
        
        # 전략별 노드 추가
        if strategy == ScrapeStrategy.AI_LEARNING:
            learn_node = GraphNode(NodeType.EXTRACT, "learn")
            learn_node.processor = self._ai_learning_processor
            graph.add_node(learn_node)
            
            graph.add_edge("fetch", "parse")
            graph.add_edge("parse", "learn")
            graph.add_edge("learn", "validate")
            
        elif strategy == ScrapeStrategy.TEMPLATE_BASED:
            extract_node = GraphNode(NodeType.EXTRACT, "extract")
            extract_node.processor = self._template_processor
            graph.add_node(extract_node)
            
            graph.add_edge("fetch", "parse")
            graph.add_edge("parse", "extract")
            graph.add_edge("extract", "validate")
            
        else:  # SMART_SCRAPER
            smart_node = GraphNode(NodeType.EXTRACT, "smart")
            smart_node.processor = self._smart_processor
            graph.add_node(smart_node)
            
            graph.add_edge("fetch", "parse")
            graph.add_edge("parse", "smart")
            graph.add_edge("smart", "validate")
        
        return graph.build()
    
    async def _select_strategy(self, config: ScrapeConfig) -> ScrapeStrategy:
        """
        최적 전략 선택
        
        Args:
            config: 스크래핑 설정
        
        Returns:
            선택된 전략
        """
        domain = urlparse(config.url).netloc
        
        # 캐시된 전략 확인
        if domain in self.domain_strategies:
            return self.domain_strategies[domain]
        
        # 템플릿 존재 여부 확인
        if domain in self.template_cache and config.use_cache:
            return ScrapeStrategy.TEMPLATE_BASED
        
        # 명시적 전략 지정
        if config.strategy != ScrapeStrategy.SMART_SCRAPER:
            return config.strategy
        
        # 기본: AI 학습
        return ScrapeStrategy.AI_LEARNING
    
    async def _fetch_page(self, url: str, headers: Optional[Dict] = None) -> str:
        """페이지 가져오기"""
        if not self._session:
            self._session = aiohttp.ClientSession()
        
        headers = headers or {
            'User-Agent': 'Mozilla/5.0 (compatible; ScrapeGraphAI/2.0)'
        }
        
        async with self._session.get(url, headers=headers) as response:
            return await response.text()
    
    async def _fetch_processor(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch 노드 프로세서"""
        config: ScrapeConfig = context['config']
        html = await self._fetch_page(config.url, config.custom_headers)
        context['html'] = html
        context['fetch_time'] = time.time()
        return context
    
    async def _parse_processor(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse 노드 프로세서"""
        html = context.get('html', '')
        soup = BeautifulSoup(html, 'lxml')
        context['soup'] = soup
        context['parse_time'] = time.time()
        
        # 콘텐츠 타입 감지
        content_type = self._detect_content_type(soup)
        context['content_type'] = content_type
        
        return context
    
    async def _ai_learning_processor(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """AI 학습 프로세서"""
        config: ScrapeConfig = context['config']
        html = context.get('html', '')
        
        template = await self.learn_structure(config.url, html)
        
        # 템플릿 기반 추출
        soup = context.get('soup')
        extracted = self._extract_with_template(soup, template)
        
        context['extracted_data'] = extracted
        context['template_id'] = self._generate_template_id(config.url)
        context['confidence'] = template.get('confidence', 0.0)
        
        return context
    
    async def _template_processor(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """템플릿 프로세서"""
        config: ScrapeConfig = context['config']
        domain = urlparse(config.url).netloc
        soup = context.get('soup')
        
        template = self.template_cache.get(domain, {})
        extracted = self._extract_with_template(soup, template)
        
        context['extracted_data'] = extracted
        context['template_id'] = self._generate_template_id(config.url)
        context['confidence'] = 0.9  # 템플릿 사용 시 높은 신뢰도
        
        return context
    
    async def _smart_processor(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """스마트 프로세서"""
        config: ScrapeConfig = context['config']
        html = context.get('html', '')
        
        # AI 직접 추출
        prompt = f"""
        Extract the following information from this webpage:
        {', '.join(config.target_fields)}
        
        HTML content:
        {html[:5000]}
        
        User request: {config.prompt}
        
        Return as structured JSON.
        """
        
        response = await self.gemini_client.analyze_content(
            prompt,
            prompt_type='structure_learning'
        )
        
        if response.status == 'success':
            context['extracted_data'] = response.data
            context['confidence'] = 0.8
        else:
            context['extracted_data'] = {}
            context['confidence'] = 0.0
        
        return context
    
    async def _validate_processor(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """검증 프로세서"""
        extracted = context.get('extracted_data', {})
        
        # 기본 검증
        is_valid = bool(extracted)
        
        # 필수 필드 검증
        required = ['title', 'content']
        for field in required:
            if field not in extracted or not extracted[field]:
                is_valid = False
                break
        
        context['is_valid'] = is_valid
        context['validation_time'] = time.time()
        
        return context
    
    def _extract_with_template(
        self, 
        soup: BeautifulSoup, 
        template: Dict[str, Any]
    ) -> Dict[str, Any]:
        """템플릿 기반 추출"""
        extracted = {}
        structure = template.get('structure', {})
        
        for field, selectors in structure.items():
            if isinstance(selectors, dict):
                css_selector = selectors.get('css_selector', '')
                if css_selector:
                    try:
                        element = soup.select_one(css_selector)
                        if element:
                            extracted[field] = element.get_text(strip=True)
                    except Exception as e:
                        self.logger.warning(f"Failed to extract {field}: {e}")
        
        return extracted
    
    def _detect_content_type(self, soup: BeautifulSoup) -> str:
        """콘텐츠 타입 감지"""
        # 간단한 휴리스틱
        if soup.find('article') or soup.find(class_=['article', 'news']):
            return ContentType.NEWS.value
        elif soup.find(class_=['blog', 'post']):
            return ContentType.BLOG.value
        elif soup.find(class_=['forum', 'thread', 'discussion']):
            return ContentType.FORUM.value
        elif '.go.kr' in str(soup) or '.gov' in str(soup):
            return ContentType.GOVERNMENT.value
        
        return ContentType.UNKNOWN.value
    
    def _generate_template_id(self, url: str) -> str:
        """템플릿 ID 생성"""
        domain = urlparse(url).netloc
        return hashlib.md5(domain.encode()).hexdigest()[:8]
