import unittest
from unittest.mock import Mock, patch, MagicMock
import json
import sys
import os

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gemini_client import GeminiClient, GeminiModel


class TestGeminiClient(unittest.TestCase):
    """Comprehensive unit tests for GeminiClient"""

    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test_api_key_12345"
        self.client = GeminiClient(api_key=self.api_key)
        self.sample_html = """
        <html>
        <head><title>연금 개혁안 발표</title></head>
        <body>
        <h1>국민연금 개혁안 주요 내용</h1>
        <p>정부가 발표한 연금 개혁안에 따르면...</p>
        <div class="content">기초연금 인상에 대한 논의가 활발합니다.</div>
        </body>
        </html>
        """
        self.sample_content = "국민연금 보험료율 인상에 대한 국민 여론이 분분합니다. 전문가들은 장기적 관점에서 필요하다고 말하지만, 일반 시민들은 부담 증가를 우려하고 있습니다."

    def test_initialization(self):
        """Test client initialization"""
        client = GeminiClient(api_key="test_key", model=GeminiModel.PRO_15.value)
        self.assertEqual(client.api_key, "test_key")
        self.assertEqual(client.model, GeminiModel.PRO_15.value)
        self.assertEqual(client.base_url, "https://generativelanguage.googleapis.com/v1beta")

    def test_extract_json_direct_parse(self):
        """Test direct JSON parsing"""
        json_text = '{"sentiment": "positive", "confidence": 0.8}'
        result = self.client._extract_json(json_text)
        self.assertEqual(result["sentiment"], "positive")
        self.assertEqual(result["confidence"], 0.8)

    def test_extract_json_markdown_format(self):
        """Test JSON extraction from markdown code blocks"""
        markdown_text = '''Here's the analysis:
        ```json
        {"sentiment": "negative", "confidence": 0.7}
        ```
        That's the result.'''
        result = self.client._extract_json(markdown_text)
        self.assertEqual(result["sentiment"], "negative")
        self.assertEqual(result["confidence"], 0.7)

    def test_extract_json_embedded(self):
        """Test JSON extraction from embedded text"""
        embedded_text = 'The analysis shows {"sentiment": "neutral", "confidence": 0.5} based on the content.'
        result = self.client._extract_json(embedded_text)
        self.assertEqual(result["sentiment"], "neutral")
        self.assertEqual(result["confidence"], 0.5)

    def test_extract_json_failure(self):
        """Test JSON extraction failure handling"""
        invalid_text = "This is not JSON at all, no brackets or anything"
        with self.assertRaises(ValueError):
            self.client._extract_json(invalid_text)

    @patch('requests.Session.post')
    def test_make_request_success(self, mock_post):
        """Test successful API request"""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{"text": "Test response"}]
                }
            }]
        }
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Test message"}]
        result = self.client._make_request(messages)
        self.assertEqual(result, "Test response")

    @patch('requests.Session.post')
    def test_make_request_failure(self, mock_post):
        """Test API request failure handling"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_post.return_value = mock_response

        messages = [{"role": "user", "content": "Test message"}]
        with self.assertRaises(Exception):
            self.client._make_request(messages)

    @patch('requests.Session.post')
    def test_analyze_pension_content_success(self, mock_post):
        """Test successful pension content analysis"""
        # Mock API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "sentiment": "negative",
                            "confidence": 0.75,
                            "relevance_score": 0.9,
                            "key_topics": ["국민연금", "보험료 인상"],
                            "summary": "국민연금 보험료 인상에 대한 부정적 여론",
                            "entities": ["국민연금공단", "보건복지부"],
                            "pension_keywords": ["보험료", "인상", "연금"],
                            "policy_impact": "high",
                            "demographic_focus": "general"
                        })
                    }]
                }
            }]
        }
        mock_post.return_value = mock_response

        result = self.client.analyze_pension_content(self.sample_content, "http://test.com")
        
        self.assertEqual(result["sentiment"], "negative")
        self.assertEqual(result["confidence"], 0.75)
        self.assertEqual(result["relevance_score"], 0.9)
        self.assertIn("국민연금", result["key_topics"])
        self.assertEqual(result["policy_impact"], "high")

    @patch('requests.Session.post')
    def test_analyze_pension_content_error_handling(self, mock_post):
        """Test pension content analysis error handling"""
        # Mock API failure
        mock_post.side_effect = Exception("API Error")

        result = self.client.analyze_pension_content(self.sample_content)
        
        # Should return default structure
        self.assertEqual(result["sentiment"], "neutral")
        self.assertEqual(result["confidence"], 0.0)
        self.assertIsInstance(result["key_topics"], list)
        self.assertIn("분석 오류", result["summary"])

    @patch('requests.Session.post')
    def test_extract_structured_data_success(self, mock_post):
        """Test successful structured data extraction"""
        target_schema = {
            "title": "string",
            "content": "string",
            "keywords": ["list"]
        }

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "title": "연금 개혁안 발표",
                            "content": "국민연금 개혁안 주요 내용",
                            "keywords": ["연금", "개혁", "정책"]
                        })
                    }]
                }
            }]
        }
        mock_post.return_value = mock_response

        result = self.client.extract_structured_data(self.sample_html, target_schema)
        
        self.assertEqual(result["title"], "연금 개혁안 발표")
        self.assertIn("연금", result["keywords"])

    @patch('requests.Session.post')
    def test_extract_structured_data_error_handling(self, mock_post):
        """Test structured data extraction error handling"""
        target_schema = {
            "title": "string",
            "content": "string",
            "keywords": ["list"]
        }

        mock_post.side_effect = Exception("API Error")

        result = self.client.extract_structured_data(self.sample_html, target_schema)
        
        # Should return schema with empty values
        self.assertEqual(result["title"], "")
        self.assertEqual(result["content"], "")
        self.assertEqual(result["keywords"], [])

    @patch('requests.Session.post')
    def test_generate_search_queries_success(self, mock_post):
        """Test successful search query generation"""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "queries": [
                                "연금 개혁 국민연금",
                                "pension reform Korea",
                                "국민연금 보험료 인상",
                                "기초연금 정책",
                                "retirement policy South Korea"
                            ]
                        })
                    }]
                }
            }]
        }
        mock_post.return_value = mock_response

        result = self.client.generate_search_queries("연금 개혁", count=5)
        
        self.assertEqual(len(result), 5)
        self.assertIn("연금 개혁 국민연금", result)
        self.assertIn("pension reform Korea", result)

    @patch('requests.Session.post')
    def test_generate_search_queries_fallback(self, mock_post):
        """Test search query generation fallback"""
        mock_post.side_effect = Exception("API Error")

        result = self.client.generate_search_queries("연금 개혁", count=3)
        
        # Should return fallback queries
        self.assertEqual(len(result), 3)
        self.assertIn("연금 개혁 국민연금", result)
        self.assertTrue(any("pension Korea" in query for query in result))

    @patch('requests.Session.post')
    def test_summarize_multiple_sources_success(self, mock_post):
        """Test successful multi-source summarization"""
        sources = [
            {
                "title": "연금 개혁안 발표",
                "url": "http://test1.com",
                "content": "정부가 연금 개혁안을 발표했습니다."
            },
            {
                "title": "시민 반응",
                "url": "http://test2.com", 
                "content": "시민들은 연금 개혁에 대해 우려를 표명했습니다."
            }
        ]

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "overall_sentiment": "mixed",
                            "confidence": 0.8,
                            "key_findings": ["정부 개혁안 발표", "시민 우려 증가"],
                            "summary": "연금 개혁안에 대한 엇갈린 반응",
                            "source_analysis": [
                                {
                                    "source": "http://test1.com",
                                    "sentiment": "neutral",
                                    "reliability": 0.9,
                                    "key_points": ["개혁안 발표"]
                                }
                            ],
                            "trending_topics": ["연금개혁", "시민반응"],
                            "policy_implications": "정책 수용성 고려 필요",
                            "recommendation": "충분한 소통과 설명 필요"
                        })
                    }]
                }
            }]
        }
        mock_post.return_value = mock_response

        result = self.client.summarize_multiple_sources(sources)
        
        self.assertEqual(result["overall_sentiment"], "mixed")
        self.assertEqual(result["confidence"], 0.8)
        self.assertIn("정부 개혁안 발표", result["key_findings"])

    @patch('requests.Session.post')
    def test_summarize_multiple_sources_error_handling(self, mock_post):
        """Test multi-source summarization error handling"""
        sources = [{"title": "Test", "url": "http://test.com", "content": "Test content"}]
        
        mock_post.side_effect = Exception("API Error")

        result = self.client.summarize_multiple_sources(sources)
        
        # Should return default structure
        self.assertEqual(result["overall_sentiment"], "neutral")
        self.assertEqual(result["confidence"], 0.0)
        self.assertIn("분석 오류", result["summary"])

    def test_different_models(self):
        """Test initialization with different models"""
        flash_client = GeminiClient(api_key="test", model=GeminiModel.FLASH_15.value)
        pro_client = GeminiClient(api_key="test", model=GeminiModel.PRO_15.value)
        vision_client = GeminiClient(api_key="test", model=GeminiModel.VISION_15.value)

        self.assertEqual(flash_client.model, "gemini-1.5-flash")
        self.assertEqual(pro_client.model, "gemini-1.5-pro")
        self.assertEqual(vision_client.model, "gemini-1.5-pro-vision")


class TestGeminiClientIntegration(unittest.TestCase):
    """Integration tests (require real API key)"""

    def setUp(self):
        """Set up integration test fixtures"""
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            self.skipTest("GEMINI_API_KEY environment variable not set")
        
        self.client = GeminiClient(api_key=self.api_key)

    def test_real_pension_analysis(self):
        """Test real pension content analysis (requires API key)"""
        content = "국민연금 보험료율을 현행 9%에서 13%로 인상하는 방안이 검토되고 있습니다."
        
        result = self.client.analyze_pension_content(content)
        
        # Verify structure
        required_keys = [
            'sentiment', 'confidence', 'relevance_score', 'key_topics',
            'summary', 'entities', 'pension_keywords', 'policy_impact', 'demographic_focus'
        ]
        for key in required_keys:
            self.assertIn(key, result)
        
        # Verify types
        self.assertIn(result['sentiment'], ['positive', 'negative', 'neutral'])
        self.assertIsInstance(result['confidence'], (int, float))
        self.assertIsInstance(result['key_topics'], list)


if __name__ == '__main__':
    # Run unit tests by default, integration tests only if API key is available
    unittest.main(verbosity=2)