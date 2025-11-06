from __future__ import annotations
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import requests
from bs4 import BeautifulSoup

from gemini_client import GeminiClient, GeminiModel


class ScrapeStrategy(Enum):
    """Scraping strategies for different content types"""
    SMART_SCRAPER = "smart_scraper"  # AI-powered content extraction  
    SEARCH_SCRAPER = "search_scraper"  # Search result scraping
    SPEECH_SCRAPER = "speech_scraper"  # Extract speech/transcript content
    STRUCTURED_SCRAPER = "structured_scraper"  # Extract structured data


@dataclass
class ScrapeRequest:
    """Scraping request configuration"""
    url: str
    prompt: str
    strategy: ScrapeStrategy = ScrapeStrategy.SMART_SCRAPER
    output_format: str = "json"
    max_retries: int = 3
    timeout: int = 30
    additional_config: Optional[Dict[str, Any]] = None


@dataclass
class ScrapeResult:
    """Scraping result with metadata"""
    success: bool
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    error: Optional[str] = None
    execution_time: float = 0.0
    tokens_used: int = 0


class ScrapeGraphAIAdapter:
    """
    Adapter that mimics ScrapeGraphAI functionality using Gemini AI
    
    This adapter provides ScrapeGraphAI-compatible interface while using
    Gemini AI for intelligent content extraction and analysis.
    """

    def __init__(self, 
                 gemini_api_key: str,
                 gemini_model: str = GeminiModel.FLASH_15.value,
                 enable_logging: bool = True):
        """
        Initialize the ScrapeGraphAI adapter
        
        Args:
            gemini_api_key: Google Gemini API key
            gemini_model: Gemini model to use
            enable_logging: Enable detailed logging
        """
        self.gemini_client = GeminiClient(api_key=gemini_api_key, model=gemini_model)
        self.logger = logging.getLogger(__name__)
        if enable_logging:
            logging.basicConfig(level=logging.INFO)
        
        # Strategy-specific prompts
        self.strategy_prompts = {
            ScrapeStrategy.SMART_SCRAPER: self._get_smart_scraper_prompt(),
            ScrapeStrategy.SEARCH_SCRAPER: self._get_search_scraper_prompt(),
            ScrapeStrategy.SPEECH_SCRAPER: self._get_speech_scraper_prompt(),
            ScrapeStrategy.STRUCTURED_SCRAPER: self._get_structured_scraper_prompt()
        }

    def _get_smart_scraper_prompt(self) -> str:
        """Get prompt for smart content scraping"""
        return """You are an expert web content extractor. 

Extract the most relevant information from the provided HTML content based on the user's specific request.

Return STRICTLY a JSON object with:
{
  "extracted_content": "main content text",
  "title": "page title",
  "summary": "brief summary",
  "key_points": ["point1", "point2"],
  "metadata": {
    "content_type": "article|news|blog|official|other",
    "language": "ko|en|other",
    "publication_date": "date if found",
    "author": "author if found"
  },
  "pension_relevance": {
    "is_relevant": true/false,
    "relevance_score": 0.0-1.0,
    "pension_keywords": ["keyword1", "keyword2"]
  }
}

Focus on extracting clean, structured content while preserving important context."""

    def _get_search_scraper_prompt(self) -> str:
        """Get prompt for search result scraping"""
        return """You are a search results analyzer. Extract search results and relevant information.

Return STRICTLY a JSON object with:
{
  "search_results": [
    {
      "title": "result title",
      "url": "result url", 
      "snippet": "description/snippet",
      "relevance_score": 0.0-1.0
    }
  ],
  "total_results": 0,
  "search_query": "inferred query",
  "related_queries": ["query1", "query2"]
}"""

    def _get_speech_scraper_prompt(self) -> str:
        """Get prompt for speech/transcript scraping"""
        return """You are a speech and transcript extractor.

Return STRICTLY a JSON object with:
{
  "transcript": "full transcript text",
  "speaker": "speaker name if identified",
  "key_quotes": ["quote1", "quote2"],
  "topics": ["topic1", "topic2"],
  "sentiment": "positive|negative|neutral",
  "summary": "brief summary of speech content"
}"""

    def _get_structured_scraper_prompt(self) -> str:
        """Get prompt for structured data scraping"""
        return """You are a structured data extractor. Extract data in the requested format.

Return the data exactly as specified in the user's schema/format request.
If no specific format is requested, use a logical JSON structure."""

    def _fetch_html_content(self, url: str, timeout: int = 30) -> str:
        """Fetch HTML content from URL"""
        try:
            response = requests.get(url, timeout=timeout, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise RuntimeError(f"Failed to fetch URL {url}: {str(e)}")

    def _clean_html_content(self, html: str, max_length: int = 8000) -> str:
        """Clean and truncate HTML content for AI processing"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "aside"]):
                script.decompose()
            
            # Extract main content
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.body or soup
            
            text = main_content.get_text(separator=' ', strip=True) if main_content else ""
            
            # Truncate if too long
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text
        except Exception:
            # Fallback: return truncated raw HTML
            return html[:max_length] + "..." if len(html) > max_length else html

    async def scrape_async(self, request: ScrapeRequest) -> ScrapeResult:
        """Asynchronously scrape content using the specified strategy"""
        return await asyncio.to_thread(self.scrape, request)

    def scrape(self, request: ScrapeRequest) -> ScrapeResult:
        """
        Scrape content using AI-powered extraction
        
        Args:
            request: Scraping request configuration
            
        Returns:
            ScrapeResult with extracted data
        """
        import time
        start_time = time.time()
        
        try:
            # Fetch HTML content
            self.logger.info(f"Fetching content from {request.url}")
            html_content = self._fetch_html_content(request.url, request.timeout)
            
            # Clean and prepare content
            cleaned_content = self._clean_html_content(html_content)
            
            # Get strategy-specific prompt
            base_prompt = self.strategy_prompts.get(request.strategy, self.strategy_prompts[ScrapeStrategy.SMART_SCRAPER])
            
            # Combine with user prompt
            combined_prompt = f"{base_prompt}\n\nUser Request: {request.prompt}\n\nContent to analyze:\n{cleaned_content}"
            
            # Use Gemini for extraction
            if request.strategy == ScrapeStrategy.SMART_SCRAPER:
                # Use pension-specific analysis
                result_data = self.gemini_client.analyze_pension_content(
                    content=cleaned_content,
                    url=request.url,
                    additional_context=request.prompt
                )
            else:
                # Use structured data extraction
                target_schema = request.additional_config or {}
                if not target_schema:
                    # Create default schema based on strategy
                    target_schema = self._get_default_schema(request.strategy)
                
                result_data = self.gemini_client.extract_structured_data(
                    html_content=cleaned_content,
                    target_schema=target_schema
                )
            
            execution_time = time.time() - start_time
            
            return ScrapeResult(
                success=True,
                data=result_data,
                metadata={
                    "url": request.url,
                    "strategy": request.strategy.value,
                    "prompt": request.prompt,
                    "content_length": len(cleaned_content),
                    "execution_time": execution_time
                },
                execution_time=execution_time,
                tokens_used=len(combined_prompt.split())  # Rough estimate
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Scraping failed for {request.url}: {str(e)}")
            
            return ScrapeResult(
                success=False,
                data={},
                metadata={
                    "url": request.url,
                    "strategy": request.strategy.value,
                    "error_type": type(e).__name__
                },
                error=str(e),
                execution_time=execution_time
            )

    def _get_default_schema(self, strategy: ScrapeStrategy) -> Dict[str, Any]:
        """Get default schema for strategy"""
        schemas = {
            ScrapeStrategy.SEARCH_SCRAPER: {
                "search_results": ["list"],
                "total_results": "number",
                "search_query": "string"
            },
            ScrapeStrategy.SPEECH_SCRAPER: {
                "transcript": "string",
                "speaker": "string",
                "key_quotes": ["list"],
                "topics": ["list"]
            },
            ScrapeStrategy.STRUCTURED_SCRAPER: {
                "title": "string",
                "content": "string",
                "metadata": {"dict": "object"}
            }
        }
        return schemas.get(strategy, {"content": "string", "title": "string"})

    def create_smart_scraper(self, prompt: str, llm_config: Optional[Dict] = None) -> 'SmartScraper':
        """Create a SmartScraper instance (ScrapeGraphAI compatibility)"""
        return SmartScraper(
            prompt=prompt,
            adapter=self,
            llm_config=llm_config or {}
        )

    def create_search_scraper(self, prompt: str, llm_config: Optional[Dict] = None) -> 'SearchScraper':
        """Create a SearchScraper instance (ScrapeGraphAI compatibility)"""
        return SearchScraper(
            prompt=prompt,
            adapter=self,
            llm_config=llm_config or {}
        )


class SmartScraper:
    """ScrapeGraphAI SmartScraper compatibility wrapper"""
    
    def __init__(self, prompt: str, adapter: ScrapeGraphAIAdapter, llm_config: Dict):
        self.prompt = prompt
        self.adapter = adapter
        self.llm_config = llm_config

    def run(self, url: str) -> Dict[str, Any]:
        """Run smart scraping (ScrapeGraphAI compatibility)"""
        request = ScrapeRequest(
            url=url,
            prompt=self.prompt,
            strategy=ScrapeStrategy.SMART_SCRAPER
        )
        result = self.adapter.scrape(request)
        return result.data if result.success else {"error": result.error}


class SearchScraper:
    """ScrapeGraphAI SearchScraper compatibility wrapper"""
    
    def __init__(self, prompt: str, adapter: ScrapeGraphAIAdapter, llm_config: Dict):
        self.prompt = prompt
        self.adapter = adapter
        self.llm_config = llm_config

    def run(self, query: str) -> Dict[str, Any]:
        """Run search scraping (ScrapeGraphAI compatibility)"""
        # For search scraping, we'll use a search engine URL pattern
        # This is a simplified approach - in production, you'd integrate with actual search APIs
        search_url = f"https://www.google.com/search?q={query}"
        
        request = ScrapeRequest(
            url=search_url,
            prompt=self.prompt,
            strategy=ScrapeStrategy.SEARCH_SCRAPER
        )
        result = self.adapter.scrape(request)
        return result.data if result.success else {"error": result.error}


# Factory functions for easy instantiation
def create_scrape_adapter(gemini_api_key: str, **kwargs) -> ScrapeGraphAIAdapter:
    """Create ScrapeGraphAI adapter with Gemini backend"""
    return ScrapeGraphAIAdapter(gemini_api_key=gemini_api_key, **kwargs)


def create_smart_scraper(prompt: str, gemini_api_key: str, **kwargs) -> SmartScraper:
    """Create SmartScraper with Gemini backend"""
    adapter = create_scrape_adapter(gemini_api_key, **kwargs)
    return adapter.create_smart_scraper(prompt)


def create_search_scraper(prompt: str, gemini_api_key: str, **kwargs) -> SearchScraper:
    """Create SearchScraper with Gemini backend"""
    adapter = create_scrape_adapter(gemini_api_key, **kwargs)
    return adapter.create_search_scraper(prompt)