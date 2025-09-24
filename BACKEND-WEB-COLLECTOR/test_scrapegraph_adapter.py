import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os
import asyncio

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scrapegraph_adapter import (
    ScrapeGraphAIAdapter, ScrapeRequest, ScrapeResult, ScrapeStrategy,
    SmartScraper, SearchScraper, create_smart_scraper, create_search_scraper
)


class TestScrapeGraphAIAdapter(unittest.TestCase):
    """Unit tests for ScrapeGraphAI adapter"""

    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test_gemini_api_key"
        self.sample_html = """
        <html>
        <head><title>연금 정책 뉴스</title></head>
        <body>
        <main>
        <h1>국민연금 보험료 인상 계획 발표</h1>
        <p>정부가 국민연금 보험료를 현행 9%에서 13%로 인상하는 계획을 발표했습니다.</p>
        <div class="content">
        이 정책은 고령화 사회에 대비한 연금 재정 안정화를 위한 조치입니다.
        </div>
        </main>
        <script>console.log('ad script');</script>
        </body>
        </html>
        """

    @patch('scrapegraph_adapter.GeminiClient')
    def test_initialization(self, mock_gemini):
        """Test adapter initialization"""
        adapter = ScrapeGraphAIAdapter(gemini_api_key=self.api_key)
        
        self.assertIsNotNone(adapter.gemini_client)
        self.assertIn(ScrapeStrategy.SMART_SCRAPER, adapter.strategy_prompts)
        mock_gemini.assert_called_once()

    @patch('requests.get')
    def test_fetch_html_content_success(self, mock_get):
        """Test successful HTML fetching"""
        # Mock successful response
        mock_response = Mock()
        mock_response.text = self.sample_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        adapter = ScrapeGraphAIAdapter(gemini_api_key=self.api_key)
        result = adapter._fetch_html_content("http://test.com")
        
        self.assertEqual(result, self.sample_html)
        mock_get.assert_called_once()

    @patch('requests.get')
    def test_fetch_html_content_failure(self, mock_get):
        """Test HTML fetching failure"""
        mock_get.side_effect = Exception("Network error")

        adapter = ScrapeGraphAIAdapter(gemini_api_key=self.api_key)
        
        with self.assertRaises(RuntimeError):
            adapter._fetch_html_content("http://test.com")

    def test_clean_html_content(self):
        """Test HTML cleaning functionality"""
        adapter = ScrapeGraphAIAdapter(gemini_api_key=self.api_key)
        
        cleaned = adapter._clean_html_content(self.sample_html)
        
        # Should remove script tags
        self.assertNotIn("console.log", cleaned)
        # Should preserve main content
        self.assertIn("국민연금 보험료 인상", cleaned)
        self.assertIn("고령화 사회", cleaned)

    def test_clean_html_content_truncation(self):
        """Test HTML content truncation"""
        adapter = ScrapeGraphAIAdapter(gemini_api_key=self.api_key)
        
        long_html = "<html><body>" + "a" * 10000 + "</body></html>"
        cleaned = adapter._clean_html_content(long_html, max_length=100)
        
        self.assertLessEqual(len(cleaned), 104)  # 100 + "..."
        self.assertTrue(cleaned.endswith("..."))

    @patch('scrapegraph_adapter.GeminiClient')
    @patch('requests.get')
    def test_scrape_smart_scraper_success(self, mock_get, mock_gemini_class):
        """Test successful smart scraping"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = self.sample_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock Gemini client
        mock_gemini = Mock()
        mock_gemini.analyze_pension_content.return_value = {
            "sentiment": "negative",
            "confidence": 0.8,
            "relevance_score": 0.9,
            "key_topics": ["국민연금", "보험료 인상"],
            "summary": "연금 보험료 인상 계획",
            "entities": ["정부", "국민연금공단"],
            "pension_keywords": ["보험료", "인상"],
            "policy_impact": "high",
            "demographic_focus": "general"
        }
        mock_gemini_class.return_value = mock_gemini

        adapter = ScrapeGraphAIAdapter(gemini_api_key=self.api_key)
        
        request = ScrapeRequest(
            url="http://test.com",
            prompt="Extract pension policy information",
            strategy=ScrapeStrategy.SMART_SCRAPER
        )
        
        result = adapter.scrape(request)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["sentiment"], "negative")
        self.assertEqual(result.data["confidence"], 0.8)
        self.assertIn("국민연금", result.data["key_topics"])

    @patch('scrapegraph_adapter.GeminiClient')
    @patch('requests.get')
    def test_scrape_structured_scraper_success(self, mock_get, mock_gemini_class):
        """Test successful structured scraping"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = self.sample_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock Gemini client
        mock_gemini = Mock()
        mock_gemini.extract_structured_data.return_value = {
            "title": "연금 정책 뉴스",
            "content": "국민연금 보험료 인상 계획 발표",
            "metadata": {"type": "news"}
        }
        mock_gemini_class.return_value = mock_gemini

        adapter = ScrapeGraphAIAdapter(gemini_api_key=self.api_key)
        
        request = ScrapeRequest(
            url="http://test.com",
            prompt="Extract structured data",
            strategy=ScrapeStrategy.STRUCTURED_SCRAPER,
            additional_config={"title": "string", "content": "string"}
        )
        
        result = adapter.scrape(request)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["title"], "연금 정책 뉴스")
        self.assertIn("content", result.data)

    @patch('scrapegraph_adapter.GeminiClient')
    @patch('requests.get')
    def test_scrape_failure_handling(self, mock_get, mock_gemini_class):
        """Test scraping failure handling"""
        mock_get.side_effect = Exception("Network error")

        adapter = ScrapeGraphAIAdapter(gemini_api_key=self.api_key)
        
        request = ScrapeRequest(
            url="http://test.com",
            prompt="Test prompt"
        )
        
        result = adapter.scrape(request)
        
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)
        self.assertIn("Network error", result.error)

    def test_get_default_schema(self):
        """Test default schema generation"""
        adapter = ScrapeGraphAIAdapter(gemini_api_key=self.api_key)
        
        search_schema = adapter._get_default_schema(ScrapeStrategy.SEARCH_SCRAPER)
        speech_schema = adapter._get_default_schema(ScrapeStrategy.SPEECH_SCRAPER)
        
        self.assertIn("search_results", search_schema)
        self.assertIn("transcript", speech_schema)

    @patch('scrapegraph_adapter.GeminiClient')
    def test_create_smart_scraper(self, mock_gemini_class):
        """Test SmartScraper creation"""
        adapter = ScrapeGraphAIAdapter(gemini_api_key=self.api_key)
        
        scraper = adapter.create_smart_scraper("Test prompt")
        
        self.assertIsInstance(scraper, SmartScraper)
        self.assertEqual(scraper.prompt, "Test prompt")
        self.assertEqual(scraper.adapter, adapter)

    @patch('scrapegraph_adapter.GeminiClient')
    def test_create_search_scraper(self, mock_gemini_class):
        """Test SearchScraper creation"""
        adapter = ScrapeGraphAIAdapter(gemini_api_key=self.api_key)
        
        scraper = adapter.create_search_scraper("Test prompt")
        
        self.assertIsInstance(scraper, SearchScraper)
        self.assertEqual(scraper.prompt, "Test prompt")
        self.assertEqual(scraper.adapter, adapter)

    @patch('scrapegraph_adapter.GeminiClient')
    @patch('requests.get')
    async def test_scrape_async(self, mock_get, mock_gemini_class):
        """Test asynchronous scraping"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = self.sample_html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock Gemini client
        mock_gemini = Mock()
        mock_gemini.analyze_pension_content.return_value = {
            "sentiment": "neutral",
            "confidence": 0.5
        }
        mock_gemini_class.return_value = mock_gemini

        adapter = ScrapeGraphAIAdapter(gemini_api_key=self.api_key)
        
        request = ScrapeRequest(
            url="http://test.com",
            prompt="Test async scraping"
        )
        
        result = await adapter.scrape_async(request)
        
        self.assertTrue(result.success)
        self.assertEqual(result.data["sentiment"], "neutral")


class TestSmartScraper(unittest.TestCase):
    """Tests for SmartScraper wrapper"""

    @patch('scrapegraph_adapter.ScrapeGraphAIAdapter')
    def test_smart_scraper_run(self, mock_adapter_class):
        """Test SmartScraper run method"""
        # Mock adapter
        mock_adapter = Mock()
        mock_result = ScrapeResult(
            success=True,
            data={"extracted_content": "Test content"},
            metadata={}
        )
        mock_adapter.scrape.return_value = mock_result
        
        scraper = SmartScraper("Test prompt", mock_adapter, {})
        result = scraper.run("http://test.com")
        
        self.assertEqual(result["extracted_content"], "Test content")
        mock_adapter.scrape.assert_called_once()

    @patch('scrapegraph_adapter.ScrapeGraphAIAdapter')
    def test_smart_scraper_run_failure(self, mock_adapter_class):
        """Test SmartScraper run method with failure"""
        # Mock adapter failure
        mock_adapter = Mock()
        mock_result = ScrapeResult(
            success=False,
            data={},
            metadata={},
            error="Test error"
        )
        mock_adapter.scrape.return_value = mock_result
        
        scraper = SmartScraper("Test prompt", mock_adapter, {})
        result = scraper.run("http://test.com")
        
        self.assertIn("error", result)
        self.assertEqual(result["error"], "Test error")


class TestSearchScraper(unittest.TestCase):
    """Tests for SearchScraper wrapper"""

    @patch('scrapegraph_adapter.ScrapeGraphAIAdapter')
    def test_search_scraper_run(self, mock_adapter_class):
        """Test SearchScraper run method"""
        # Mock adapter
        mock_adapter = Mock()
        mock_result = ScrapeResult(
            success=True,
            data={"search_results": [{"title": "Test result"}]},
            metadata={}
        )
        mock_adapter.scrape.return_value = mock_result
        
        scraper = SearchScraper("Test prompt", mock_adapter, {})
        result = scraper.run("pension reform Korea")
        
        self.assertIn("search_results", result)
        mock_adapter.scrape.assert_called_once()
        
        # Verify that search URL was constructed
        call_args = mock_adapter.scrape.call_args[0][0]  # Get ScrapeRequest
        self.assertIn("google.com/search", call_args.url)
        self.assertEqual(call_args.strategy, ScrapeStrategy.SEARCH_SCRAPER)


class TestFactoryFunctions(unittest.TestCase):
    """Tests for factory functions"""

    @patch('scrapegraph_adapter.GeminiClient')
    def test_create_smart_scraper_factory(self, mock_gemini):
        """Test create_smart_scraper factory function"""
        scraper = create_smart_scraper("Test prompt", "test_api_key")
        
        self.assertIsInstance(scraper, SmartScraper)
        self.assertEqual(scraper.prompt, "Test prompt")

    @patch('scrapegraph_adapter.GeminiClient')
    def test_create_search_scraper_factory(self, mock_gemini):
        """Test create_search_scraper factory function"""
        scraper = create_search_scraper("Test prompt", "test_api_key")
        
        self.assertIsInstance(scraper, SearchScraper)
        self.assertEqual(scraper.prompt, "Test prompt")


if __name__ == '__main__':
    unittest.main(verbosity=2)