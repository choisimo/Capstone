"""
AI 기반 웹페이지 구조 학습 시스템
"""
import asyncio
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlparse
from dataclasses import dataclass, field
from bs4 import BeautifulSoup, Tag
import re
from collections import Counter

from gemini_client_v2 import GeminiClientV2
from prompts.structure import AdaptiveStructureLearningPromptTemplate
from parsers.structured_parser import StructuredDataParser

logger = logging.getLogger(__name__)


@dataclass
class ExtractionTemplate:
    """추출 템플릿"""
    template_id: str
    domain: str
    url_pattern: str
    selectors: Dict[str, Dict[str, Any]]
    confidence: float
    created_at: datetime
    updated_at: datetime
    usage_count: int = 0
    success_rate: float = 1.0
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "template_id": self.template_id,
            "domain": self.domain,
            "url_pattern": self.url_pattern,
            "selectors": self.selectors,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "version": self.version,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtractionTemplate':
        """딕셔너리에서 생성"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class PatternDetector:
    """웹페이지 패턴 감지기"""
    
    def __init__(self):
        self.common_patterns = {
            'news': {
                'article_container': ['article', 'main', '.article-body', '#content'],
                'title': ['h1', '.title', '.headline', '.article-title'],
                'author': ['.author', '.byline', '.writer', 'span.author'],
                'date': ['time', '.date', '.publish-date', '.timestamp'],
                'content': ['.content', '.body', '.text', 'p']
            },
            'blog': {
                'post_container': ['.post', '.entry', 'article', '.blog-post'],
                'title': ['h1', 'h2.title', '.post-title', '.entry-title'],
                'author': ['.author', '.by', '.posted-by'],
                'date': ['.date', 'time', '.published'],
                'content': ['.content', '.entry-content', '.post-content']
            },
            'forum': {
                'thread_container': ['.thread', '.topic', '.discussion'],
                'title': ['.subject', 'h1', '.topic-title'],
                'author': ['.username', '.poster', '.author'],
                'date': ['.post-time', '.timestamp'],
                'content': ['.post-body', '.message', '.text']
            }
        }
    
    def detect_page_type(self, soup: BeautifulSoup) -> str:
        """페이지 타입 감지"""
        scores = {}
        
        for page_type, patterns in self.common_patterns.items():
            score = 0
            for selector_type, selectors in patterns.items():
                for selector in selectors:
                    if soup.select(selector):
                        score += 1
            scores[page_type] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'unknown'
    
    def find_repeating_structures(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """반복 구조 찾기"""
        repeating = []
        
        # 클래스명 기반 반복 요소 찾기
        all_elements = soup.find_all(True, {'class': True})
        class_counter = Counter()
        
        for elem in all_elements:
            classes = elem.get('class', [])
            for cls in classes:
                class_counter[cls] += 1
        
        # 3개 이상 반복되는 클래스
        for cls, count in class_counter.items():
            if count >= 3:
                elements = soup.find_all(class_=cls)
                if elements:
                    repeating.append({
                        'selector': f'.{cls}',
                        'count': count,
                        'type': 'class',
                        'sample': str(elements[0])[:200]
                    })
        
        return repeating
    
    def analyze_structure_similarity(
        self, 
        template1: Dict[str, Any], 
        template2: Dict[str, Any]
    ) -> float:
        """구조 유사도 분석"""
        if not template1 or not template2:
            return 0.0
        
        selectors1 = set(template1.get('selectors', {}).keys())
        selectors2 = set(template2.get('selectors', {}).keys())
        
        if not selectors1 or not selectors2:
            return 0.0
        
        intersection = selectors1.intersection(selectors2)
        union = selectors1.union(selectors2)
        
        return len(intersection) / len(union) if union else 0.0


class TemplateLearner:
    """
    AI 기반 템플릿 학습 시스템
    
    웹페이지 구조를 학습하고 추출 템플릿을 생성/관리
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_client = GeminiClientV2(api_key=gemini_api_key)
        self.prompt_template = AdaptiveStructureLearningPromptTemplate()
        self.parser = StructuredDataParser()
        self.pattern_detector = PatternDetector()
        
        # 템플릿 저장소
        self.templates: Dict[str, ExtractionTemplate] = {}
        self.domain_templates: Dict[str, List[str]] = {}  # 도메인별 템플릿 ID
        
        # 학습 히스토리
        self.learning_history: List[Dict[str, Any]] = []
        
        self.logger = logger
    
    async def learn(
        self, 
        url: str, 
        html: str,
        target_fields: Optional[List[str]] = None
    ) -> ExtractionTemplate:
        """
        웹페이지 구조 학습
        
        Args:
            url: 웹페이지 URL
            html: HTML 콘텐츠
            target_fields: 추출 대상 필드
        
        Returns:
            학습된 템플릿
        """
        start_time = datetime.utcnow()
        soup = BeautifulSoup(html, 'lxml')
        
        # 페이지 타입 감지
        page_type = self.pattern_detector.detect_page_type(soup)
        self.logger.info(f"Detected page type: {page_type}")
        
        # 기존 템플릿 확인
        domain = urlparse(url).netloc
        existing_template = await self._find_similar_template(domain, soup)
        
        if existing_template and existing_template.confidence > 0.8:
            self.logger.info(f"Using existing template: {existing_template.template_id}")
            return existing_template
        
        # AI 구조 학습
        learning_result = await self._ai_structure_learning(
            url, html, page_type, target_fields
        )
        
        # 템플릿 생성
        template = self._create_template(
            url, 
            learning_result,
            page_type
        )
        
        # 템플릿 최적화
        template = await self._optimize_template(template, soup)
        
        # 저장
        self._save_template(template)
        
        # 히스토리 기록
        self.learning_history.append({
            "url": url,
            "template_id": template.template_id,
            "timestamp": start_time,
            "duration": (datetime.utcnow() - start_time).total_seconds(),
            "success": True
        })
        
        return template
    
    async def _ai_structure_learning(
        self,
        url: str,
        html: str,
        page_type: str,
        target_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """AI 기반 구조 학습"""
        # 프롬프트 생성
        prompt = self.prompt_template.format_prompt(
            html[:10000],  # 처음 10KB만 사용
            url=url,
            page_type=page_type,
            target_fields=target_fields
        )
        
        # AI 분석
        response = await self.gemini_client.analyze_content(
            prompt,
            prompt_type='structure_learning'
        )
        
        if response.status == 'success':
            return response.data
        
        return {}
    
    def _create_template(
        self,
        url: str,
        learning_result: Dict[str, Any],
        page_type: str
    ) -> ExtractionTemplate:
        """템플릿 생성"""
        domain = urlparse(url).netloc
        template_id = self._generate_template_id(url)
        
        # 셀렉터 추출
        selectors = {}
        structure = learning_result.get('structure', {})
        
        for field, selector_info in structure.items():
            if isinstance(selector_info, dict):
                selectors[field] = {
                    'css': selector_info.get('css_selector', ''),
                    'xpath': selector_info.get('xpath', ''),
                    'attribute': selector_info.get('attribute', 'text'),
                    'confidence': selector_info.get('confidence', 0.5),
                    'fallback': selector_info.get('fallback_selectors', [])
                }
            elif isinstance(selector_info, str):
                selectors[field] = {
                    'css': selector_info,
                    'xpath': '',
                    'attribute': 'text',
                    'confidence': 0.5,
                    'fallback': []
                }
        
        # 템플릿 생성
        template = ExtractionTemplate(
            template_id=template_id,
            domain=domain,
            url_pattern=self._generate_url_pattern(url),
            selectors=selectors,
            confidence=learning_result.get('confidence', 0.5),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={
                'page_type': page_type,
                'extraction_hints': learning_result.get('extraction_hints', []),
                'potential_issues': learning_result.get('potential_issues', [])
            }
        )
        
        return template
    
    async def _optimize_template(
        self,
        template: ExtractionTemplate,
        soup: BeautifulSoup
    ) -> ExtractionTemplate:
        """템플릿 최적화"""
        optimized_selectors = {}
        
        for field, selector_info in template.selectors.items():
            css_selector = selector_info.get('css', '')
            
            if css_selector:
                # 셀렉터 테스트
                elements = soup.select(css_selector)
                
                if elements:
                    # 성공 - 더 구체적인 셀렉터 생성
                    optimized = self._optimize_selector(elements[0], soup)
                    optimized_selectors[field] = {
                        **selector_info,
                        'css': optimized,
                        'tested': True,
                        'element_count': len(elements)
                    }
                else:
                    # 실패 - 폴백 시도
                    fallback = self._find_fallback_selector(field, soup)
                    if fallback:
                        optimized_selectors[field] = {
                            **selector_info,
                            'css': fallback,
                            'tested': True,
                            'fallback_used': True
                        }
                    else:
                        optimized_selectors[field] = selector_info
            else:
                optimized_selectors[field] = selector_info
        
        template.selectors = optimized_selectors
        return template
    
    def _optimize_selector(self, element: Tag, soup: BeautifulSoup) -> str:
        """셀렉터 최적화"""
        # ID가 있으면 ID 사용
        if element.get('id'):
            return f'#{element.get("id")}'
        
        # 클래스가 있으면 클래스 조합
        classes = element.get('class', [])
        if classes:
            class_selector = '.' + '.'.join(classes)
            # 유일성 테스트
            if len(soup.select(class_selector)) == 1:
                return class_selector
        
        # 부모와 조합
        parent = element.parent
        if parent and parent.name != 'html':
            parent_selector = self._get_simple_selector(parent)
            child_selector = self._get_simple_selector(element)
            combined = f'{parent_selector} > {child_selector}'
            
            if len(soup.select(combined)) == 1:
                return combined
        
        # 기본 셀렉터
        return self._get_simple_selector(element)
    
    def _get_simple_selector(self, element: Tag) -> str:
        """단순 셀렉터 생성"""
        selector = element.name
        
        if element.get('id'):
            selector += f'#{element.get("id")}'
        elif element.get('class'):
            selector += '.' + '.'.join(element.get('class'))
        
        return selector
    
    def _find_fallback_selector(self, field: str, soup: BeautifulSoup) -> Optional[str]:
        """폴백 셀렉터 찾기"""
        # 필드별 공통 패턴
        common_patterns = {
            'title': ['h1', 'h2', '.title', '#title', '[class*="title"]'],
            'content': ['article', '.content', '.body', 'main', '[class*="content"]'],
            'author': ['.author', '.by', '[class*="author"]', '[class*="writer"]'],
            'date': ['time', '.date', '[class*="date"]', '[class*="time"]'],
            'category': ['.category', '.tag', '[class*="category"]', '[class*="tag"]']
        }
        
        patterns = common_patterns.get(field, [])
        
        for pattern in patterns:
            elements = soup.select(pattern)
            if elements:
                return pattern
        
        return None
    
    async def _find_similar_template(
        self,
        domain: str,
        soup: BeautifulSoup
    ) -> Optional[ExtractionTemplate]:
        """유사한 템플릿 찾기"""
        if domain not in self.domain_templates:
            return None
        
        template_ids = self.domain_templates[domain]
        best_match = None
        best_score = 0.0
        
        for template_id in template_ids:
            template = self.templates.get(template_id)
            if template:
                # 템플릿 테스트
                score = self._test_template(template, soup)
                if score > best_score:
                    best_score = score
                    best_match = template
        
        if best_score > 0.7:  # 70% 이상 일치
            return best_match
        
        return None
    
    def _test_template(
        self,
        template: ExtractionTemplate,
        soup: BeautifulSoup
    ) -> float:
        """템플릿 테스트"""
        matches = 0
        total = len(template.selectors)
        
        if total == 0:
            return 0.0
        
        for field, selector_info in template.selectors.items():
            css_selector = selector_info.get('css', '')
            if css_selector:
                elements = soup.select(css_selector)
                if elements:
                    matches += 1
        
        return matches / total
    
    def _save_template(self, template: ExtractionTemplate):
        """템플릿 저장"""
        self.templates[template.template_id] = template
        
        # 도메인별 인덱싱
        if template.domain not in self.domain_templates:
            self.domain_templates[template.domain] = []
        
        if template.template_id not in self.domain_templates[template.domain]:
            self.domain_templates[template.domain].append(template.template_id)
    
    def _generate_template_id(self, url: str) -> str:
        """템플릿 ID 생성"""
        domain = urlparse(url).netloc
        path = urlparse(url).path
        
        # 도메인과 경로 패턴 기반 ID
        pattern = f"{domain}{path}"
        return hashlib.md5(pattern.encode()).hexdigest()[:12]
    
    def _generate_url_pattern(self, url: str) -> str:
        """URL 패턴 생성"""
        parsed = urlparse(url)
        path = parsed.path
        
        # 숫자를 와일드카드로 변경
        pattern = re.sub(r'\d+', '*', path)
        
        return f"{parsed.scheme}://{parsed.netloc}{pattern}"
    
    async def update_template(
        self,
        template_id: str,
        feedback: Dict[str, Any]
    ) -> bool:
        """템플릿 업데이트"""
        if template_id not in self.templates:
            return False
        
        template = self.templates[template_id]
        
        # 사용 횟수 증가
        template.usage_count += 1
        
        # 성공률 업데이트
        if 'success' in feedback:
            success_rate = template.success_rate
            new_rate = (success_rate * (template.usage_count - 1) + 
                       (1.0 if feedback['success'] else 0.0)) / template.usage_count
            template.success_rate = new_rate
        
        # 셀렉터 업데이트
        if 'failed_selectors' in feedback:
            for field in feedback['failed_selectors']:
                if field in template.selectors:
                    template.selectors[field]['confidence'] *= 0.9
        
        template.updated_at = datetime.utcnow()
        
        # 버전 증가 (major update)
        if template.success_rate < 0.5:
            template.version += 1
            self.logger.warning(f"Template {template_id} performance degraded, version bumped")
        
        return True
    
    def get_template(self, template_id: str) -> Optional[ExtractionTemplate]:
        """템플릿 조회"""
        return self.templates.get(template_id)
    
    def get_domain_templates(self, domain: str) -> List[ExtractionTemplate]:
        """도메인별 템플릿 조회"""
        template_ids = self.domain_templates.get(domain, [])
        return [self.templates[tid] for tid in template_ids if tid in self.templates]
    
    def export_templates(self) -> Dict[str, Any]:
        """템플릿 내보내기"""
        return {
            'templates': {
                tid: template.to_dict() 
                for tid, template in self.templates.items()
            },
            'domain_index': self.domain_templates,
            'export_time': datetime.utcnow().isoformat()
        }
    
    def import_templates(self, data: Dict[str, Any]) -> int:
        """템플릿 가져오기"""
        count = 0
        
        templates_data = data.get('templates', {})
        for tid, template_data in templates_data.items():
            try:
                template = ExtractionTemplate.from_dict(template_data)
                self.templates[tid] = template
                count += 1
            except Exception as e:
                self.logger.error(f"Failed to import template {tid}: {e}")
        
        # 도메인 인덱스 재구성
        self.domain_templates = data.get('domain_index', {})
        
        return count
