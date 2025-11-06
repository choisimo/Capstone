"""
Integration test for the enhanced collector service

This test validates the integration between:
- Gemini AI client
- ScrapeGraphAI adapter  
- Enhanced collector service with hybrid functionality
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os
import asyncio

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gemini_client import GeminiClient
from scrapegraph_adapter import ScrapeGraphAIAdapter, ScrapeRequest, ScrapeStrategy


class TestHybridCollectorIntegration(unittest.TestCase):
    """Integration tests for hybrid collector components"""

    def setUp(self):
        """Set up test fixtures"""
        self.gemini_api_key = "test_gemini_key"
        self.test_url = "https://www.nps.or.kr/jsppage/info/easy/easy_01_01.jsp"
        self.test_content = """
        <html>
        <head><title>국민연금 보험료 인상 발표</title></head>
        <body>
        <article>
        <h1>정부, 국민연금 보험료율 13%로 인상 계획 발표</h1>
        <p>정부가 국민연금의 장기 지속가능성을 위해 보험료율을 현행 9%에서 13%로 
        단계적으로 인상하는 계획을 발표했습니다.</p>
        <p>이번 개혁안은 급속한 고령화와 저출산으로 인한 연금 재정 악화에 대응하기 위한 
        불가피한 조치라고 정부는 설명했습니다.</p>
        <div class="quote">
        "국민연금의 지속가능성 확보를 위해서는 보험료 인상이 필요합니다" - 보건복지부 장관
        </div>
        </article>
        </body>
        </html>
        """

    @patch('scrapegraph_adapter.GeminiClient')
    @patch('requests.get')
    def test_end_to_end_pension_analysis(self, mock_get, mock_gemini_class):
        """Test complete end-to-end pension content analysis"""
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = self.test_content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock Gemini client responses
        mock_gemini = Mock()
        
        # Mock pension analysis response
        mock_gemini.analyze_pension_content.return_value = {
            "sentiment": "negative",
            "confidence": 0.85,
            "relevance_score": 0.95,
            "key_topics": ["국민연금", "보험료 인상", "연금개혁"],
            "summary": "국민연금 보험료 인상 계획에 대한 정부 발표 내용",
            "entities": ["정부", "보건복지부", "국민연금공단"],
            "pension_keywords": ["보험료", "인상", "지속가능성", "고령화"],
            "policy_impact": "high",
            "demographic_focus": "general"
        }
        
        # Mock search query generation
        mock_gemini.generate_search_queries.return_value = [
            "국민연금 보험료 인상 2024",
            "연금개혁 정부 계획",
            "pension reform Korea 2024",
            "국민연금 지속가능성 정책",
            "보험료율 인상 반응"
        ]
        
        mock_gemini_class.return_value = mock_gemini

        # Test ScrapeGraphAI adapter
        adapter = ScrapeGraphAIAdapter(gemini_api_key=self.gemini_api_key)
        
        # Test smart scraping
        request = ScrapeRequest(
            url=self.test_url,
            prompt="Extract pension policy information and analyze sentiment",
            strategy=ScrapeStrategy.SMART_SCRAPER
        )
        
        result = adapter.scrape(request)
        
        # Verify results
        self.assertTrue(result.success)
        self.assertEqual(result.data["sentiment"], "negative")
        self.assertEqual(result.data["confidence"], 0.85)
        self.assertIn("국민연금", result.data["key_topics"])
        self.assertEqual(result.data["policy_impact"], "high")
        
        # Verify metadata
        self.assertIn("url", result.metadata)
        self.assertIn("strategy", result.metadata)
        self.assertEqual(result.metadata["strategy"], "smart_scraper")

    @patch('scrapegraph_adapter.GeminiClient')
    def test_search_query_generation_integration(self, mock_gemini_class):
        """Test search query generation for pension topics"""
        
        # Mock Gemini client
        mock_gemini = Mock()
        mock_gemini.generate_search_queries.return_value = [
            "연금개혁 최신 동향",
            "pension reform latest news",
            "국민연금 정책 변화",
            "기초연금 인상 소식",
            "개인연금 세제혜택"
        ]
        mock_gemini_class.return_value = mock_gemini

        # Test direct Gemini integration
        gemini_client = GeminiClient(api_key=self.gemini_api_key)
        
        queries = gemini_client.generate_search_queries("연금개혁", count=5)
        
        self.assertEqual(len(queries), 5)
        self.assertIn("연금개혁 최신 동향", queries)
        self.assertIn("pension reform latest news", queries)

    @patch('scrapegraph_adapter.GeminiClient')
    @patch('requests.get')
    def test_multi_source_analysis_integration(self, mock_get, mock_gemini_class):
        """Test multi-source content analysis"""
        
        # Mock HTTP responses for multiple sources
        sources = [
            {
                "title": "정부 연금개혁안 발표",
                "url": "http://test1.com",
                "content": "정부가 국민연금 보험료 인상을 발표했습니다."
            },
            {
                "title": "시민단체 반대 성명",
                "url": "http://test2.com",
                "content": "시민단체들이 연금 보험료 인상에 강력 반대한다고 밝혔습니다."
            },
            {
                "title": "전문가 분석",
                "url": "http://test3.com",
                "content": "경제 전문가들은 장기적으로 불가피한 조치라고 분석했습니다."
            }
        ]

        # Mock Gemini client
        mock_gemini = Mock()
        mock_gemini.summarize_multiple_sources.return_value = {
            "overall_sentiment": "mixed",
            "confidence": 0.8,
            "key_findings": [
                "정부의 보험료 인상 발표",
                "시민단체의 강력한 반대",
                "전문가들의 장기적 필요성 인정"
            ],
            "summary": "연금 보험료 인상에 대한 다양한 입장이 표출되고 있음",
            "source_analysis": [
                {
                    "source": "http://test1.com",
                    "sentiment": "neutral",
                    "reliability": 0.9,
                    "key_points": ["정부 발표", "보험료 인상"]
                },
                {
                    "source": "http://test2.com",
                    "sentiment": "negative",
                    "reliability": 0.7,
                    "key_points": ["시민 반대", "부담 증가"]
                }
            ],
            "trending_topics": ["연금개혁", "보험료인상", "시민반응"],
            "policy_implications": "정책 수용성 제고 필요",
            "recommendation": "단계적 인상과 충분한 소통 필요"
        }
        mock_gemini_class.return_value = mock_gemini

        # Test multi-source analysis
        gemini_client = GeminiClient(api_key=self.gemini_api_key)
        
        result = gemini_client.summarize_multiple_sources(sources)
        
        # Verify comprehensive analysis
        self.assertEqual(result["overall_sentiment"], "mixed")
        self.assertEqual(len(result["key_findings"]), 3)
        self.assertIn("연금개혁", result["trending_topics"])
        self.assertEqual(len(result["source_analysis"]), 2)

    @patch('scrapegraph_adapter.GeminiClient')
    @patch('requests.get')
    def test_strategy_based_scraping(self, mock_get, mock_gemini_class):
        """Test different scraping strategies"""
        
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = self.test_content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock Gemini client
        mock_gemini = Mock()
        
        # Different responses for different strategies
        mock_gemini.analyze_pension_content.return_value = {
            "sentiment": "negative",
            "confidence": 0.8,
            "key_topics": ["연금개혁"]
        }
        
        mock_gemini.extract_structured_data.return_value = {
            "title": "국민연금 보험료 인상 발표",
            "content": "정부가 보험료 인상 계획을 발표",
            "author": "보건복지부",
            "date": "2024-09-24"
        }
        
        mock_gemini_class.return_value = mock_gemini

        adapter = ScrapeGraphAIAdapter(gemini_api_key=self.gemini_api_key)
        
        # Test Smart Scraper strategy
        smart_request = ScrapeRequest(
            url=self.test_url,
            prompt="Analyze pension content",
            strategy=ScrapeStrategy.SMART_SCRAPER
        )
        smart_result = adapter.scrape(smart_request)
        
        self.assertTrue(smart_result.success)
        self.assertIn("sentiment", smart_result.data)
        
        # Test Structured Scraper strategy
        structured_request = ScrapeRequest(
            url=self.test_url,
            prompt="Extract structured data",
            strategy=ScrapeStrategy.STRUCTURED_SCRAPER,
            additional_config={
                "title": "string",
                "content": "string",
                "author": "string"
            }
        )
        structured_result = adapter.scrape(structured_request)
        
        self.assertTrue(structured_result.success)
        self.assertIn("title", structured_result.data)
        self.assertIn("author", structured_result.data)

    def test_error_handling_and_fallbacks(self):
        """Test error handling and fallback mechanisms"""
        
        # Test with invalid API key
        adapter = ScrapeGraphAIAdapter(gemini_api_key="invalid_key")
        
        request = ScrapeRequest(
            url="http://invalid-url.com",
            prompt="Test prompt"
        )
        
        # Should handle errors gracefully
        result = adapter.scrape(request)
        
        # Should fail gracefully with error information
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error)
        self.assertIn("url", result.metadata)

    def test_configuration_integration(self):
        """Test configuration loading and validation"""
        
        # Test environment variable integration
        original_env = os.environ.copy()
        
        try:
            # Set test environment variables
            os.environ["GEMINI_API_KEY"] = "test_key_123"
            os.environ["GEMINI_MODEL"] = "gemini-1.5-pro"
            os.environ["ENABLE_AI"] = "1"
            os.environ["ENABLE_SMART_SCRAPING"] = "1"
            
            # Import should pick up environment variables
            from hybrid_collector_service import GeminiConfig, HybridConfig
            
            gemini_config = GeminiConfig.from_env()
            hybrid_config = HybridConfig.from_env()
            
            self.assertEqual(gemini_config.api_key, "test_key_123")
            self.assertEqual(gemini_config.model, "gemini-1.5-pro")
            self.assertTrue(hybrid_config.enable_ai)
            self.assertTrue(hybrid_config.enable_smart_scraping)
            
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)


if __name__ == '__main__':
    unittest.main(verbosity=2)