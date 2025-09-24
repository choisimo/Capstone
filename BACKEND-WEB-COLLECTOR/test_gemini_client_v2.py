"""
Gemini Client V2 테스트 스위트
"""
import unittest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gemini_client_v2 import GeminiClientV2, GeminiModel, AnalysisRequest, AnalysisResponse


class TestGeminiClientV2(unittest.TestCase):
    """GeminiClientV2 종합 테스트"""
    
    def setUp(self):
        """테스트 픽스처 설정"""
        self.api_key = "test_api_key_12345"
        os.environ["GEMINI_API_KEY"] = self.api_key
        self.client = GeminiClientV2()
        
        self.sample_content = """
        국민연금 보험료율 인상에 대한 국민 여론이 분분합니다. 
        전문가들은 장기적 관점에서 필요하다고 말하지만, 
        일반 시민들은 부담 증가를 우려하고 있습니다.
        """
        
        self.sample_html = """
        <html>
        <head><title>연금 개혁안 발표</title></head>
        <body>
        <h1 class="article-title">국민연금 개혁안 주요 내용</h1>
        <div class="article-body">
            <p>정부가 발표한 연금 개혁안에 따르면...</p>
        </div>
        <span class="author-name">김기자</span>
        <time datetime="2025-09-24">2025년 9월 24일</time>
        </body>
        </html>
        """
    
    def test_initialization(self):
        """클라이언트 초기화 테스트"""
        client = GeminiClientV2(api_key="test_key")
        self.assertEqual(client.api_key, "test_key")
        self.assertEqual(client.default_model, GeminiModel.FLASH_15.value)
        self.assertIn(GeminiModel.FLASH_15.value, client.models)
        self.assertIn(GeminiModel.PRO_15.value, client.models)
    
    def test_initialization_from_env(self):
        """환경변수로부터 초기화 테스트"""
        os.environ["GEMINI_API_KEY"] = "env_test_key"
        client = GeminiClientV2()
        self.assertEqual(client.api_key, "env_test_key")
    
    def test_initialization_no_key(self):
        """API 키 없이 초기화 시 에러 테스트"""
        os.environ.pop("GEMINI_API_KEY", None)
        with self.assertRaises(ValueError) as context:
            GeminiClientV2()
        self.assertIn("API key is required", str(context.exception))
    
    def test_parse_response_direct_json(self):
        """직접 JSON 파싱 테스트"""
        json_text = '{"sentiment": "positive", "confidence": 0.8}'
        result = self.client._parse_response(json_text, "sentiment")
        self.assertEqual(result["sentiment"], "positive")
        self.assertEqual(result["confidence"], 0.8)
    
    def test_parse_response_markdown_format(self):
        """마크다운 코드 블록에서 JSON 추출 테스트"""
        markdown_text = '''Here's the analysis:
        ```json
        {"sentiment": "negative", "confidence": 0.7, "emotions": ["worry", "frustration"]}
        ```
        '''
        result = self.client._parse_response(markdown_text, "sentiment")
        self.assertEqual(result["sentiment"], "negative")
        self.assertEqual(result["confidence"], 0.7)
        self.assertIn("worry", result["emotions"])
    
    def test_parse_response_mixed_content(self):
        """혼합 콘텐츠에서 JSON 추출 테스트"""
        mixed_text = '''
        The analysis shows interesting results.
        {"sentiment": "neutral", "score": 0.0, "confidence": 0.9}
        Additional commentary here.
        '''
        result = self.client._parse_response(mixed_text, "sentiment")
        self.assertEqual(result["sentiment"], "neutral")
        self.assertEqual(result["score"], 0.0)
    
    def test_parse_response_error_handling(self):
        """파싱 실패 시 에러 처리 테스트"""
        invalid_text = "This is not JSON at all"
        result = self.client._parse_response(invalid_text, "sentiment")
        self.assertTrue(result.get("parse_error"))
        self.assertIn("error_message", result)
        self.assertEqual(result["prompt_type"], "sentiment")
    
    @patch('gemini_client_v2.genai.GenerativeModel')
    def test_analyze_content_async(self, mock_model_class):
        """비동기 콘텐츠 분석 테스트"""
        # Mock 설정
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"overall_sentiment": "negative", "sentiment_score": -0.6, "confidence": 0.85}'
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        # 비동기 테스트 실행
        async def run_test():
            response = await self.client.analyze_content(
                self.sample_content,
                prompt_type="sentiment"
            )
            return response
        
        # 테스트 실행
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(run_test())
        
        self.assertEqual(response.status, "success")
        self.assertEqual(response.data["overall_sentiment"], "negative")
        self.assertEqual(response.data["sentiment_score"], -0.6)
    
    def test_sentiment_prompt_generation(self):
        """감성 분석 프롬프트 생성 테스트"""
        prompt = self.client._get_sentiment_prompt(self.sample_content)
        self.assertIn("감성을 분석", prompt)
        self.assertIn(self.sample_content, prompt)
        self.assertIn("overall_sentiment", prompt)
        self.assertIn("sentiment_score", prompt)
    
    def test_absa_prompt_generation(self):
        """ABSA 프롬프트 생성 테스트"""
        prompt = self.client._get_absa_prompt(self.sample_content)
        self.assertIn("aspect별 감성", prompt)
        self.assertIn("연금", prompt)
        self.assertIn(self.sample_content, prompt)
    
    def test_pension_sentiment_prompt_generation(self):
        """연금 감성 분석 프롬프트 생성 테스트"""
        prompt = self.client._get_pension_sentiment_prompt(self.sample_content)
        self.assertIn("연금 관련 감성", prompt)
        self.assertIn("국민연금", prompt)
        self.assertIn("연금개혁", prompt)
        self.assertIn("trust_level", prompt)
    
    def test_structure_learning_prompt(self):
        """구조 학습 프롬프트 생성 테스트"""
        prompt = self.client._get_structure_learning_prompt(self.sample_html)
        self.assertIn("HTML 구조", prompt)
        self.assertIn("CSS 셀렉터", prompt)
        self.assertIn("title", prompt)
        self.assertIn("content", prompt)
    
    def test_change_analysis_prompt(self):
        """변경 분석 프롬프트 생성 테스트"""
        prompt = self.client._get_change_analysis_prompt("변경 내용")
        self.assertIn("변경사항을 분석", prompt)
        self.assertIn("change_type", prompt)
        self.assertIn("importance_score", prompt)
    
    def test_analysis_request_validation(self):
        """분석 요청 모델 검증 테스트"""
        request = AnalysisRequest(
            content=self.sample_content,
            prompt_type="sentiment",
            temperature=0.5,
            max_tokens=1024
        )
        self.assertEqual(request.content, self.sample_content)
        self.assertEqual(request.temperature, 0.5)
        self.assertEqual(request.max_tokens, 1024)
    
    def test_analysis_response_model(self):
        """분석 응답 모델 테스트"""
        response = AnalysisResponse(
            status="success",
            model=GeminiModel.FLASH_15.value,
            timestamp=datetime.utcnow().isoformat(),
            data={"sentiment": "positive"}
        )
        self.assertEqual(response.status, "success")
        self.assertIn("sentiment", response.data)
    
    @patch('gemini_client_v2.genai.GenerativeModel')
    def test_batch_analyze(self, mock_model_class):
        """배치 분석 테스트"""
        # Mock 설정
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '{"overall_sentiment": "neutral", "confidence": 0.7}'
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        # 테스트 데이터
        contents = ["Content 1", "Content 2", "Content 3"]
        
        # 비동기 테스트
        async def run_test():
            results = await self.client.batch_analyze(
                contents,
                prompt_type="sentiment",
                batch_size=2
            )
            return results
        
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(run_test())
        
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result, AnalysisResponse)
    
    @patch('gemini_client_v2.genai.GenerativeModel')
    def test_analyze_change(self, mock_model_class):
        """변경사항 분석 테스트"""
        # Mock 설정
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '''{
            "change_type": "major",
            "importance_score": 8,
            "sentiment_shift": -0.3
        }'''
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        before = "이전 콘텐츠"
        after = "변경된 콘텐츠"
        
        async def run_test():
            result = await self.client.analyze_change(before, after)
            return result
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(run_test())
        
        self.assertEqual(result.get("change_type"), "major")
        self.assertEqual(result.get("importance_score"), 8)
    
    def test_context_manager(self):
        """비동기 컨텍스트 매니저 테스트"""
        async def run_test():
            async with GeminiClientV2() as client:
                self.assertIsNotNone(client._session)
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_test())
    
    def test_error_handling_api_failure(self):
        """API 실패 시 에러 처리 테스트"""
        async def run_test():
            with patch('gemini_client_v2.asyncio.to_thread', side_effect=Exception("API Error")):
                response = await self.client.analyze_content("test", "sentiment")
                self.assertEqual(response.status, "error")
                self.assertIn("API Error", response.error)
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(run_test())


class TestGeminiModelEnum(unittest.TestCase):
    """GeminiModel Enum 테스트"""
    
    def test_model_values(self):
        """모델 값 테스트"""
        self.assertEqual(GeminiModel.FLASH_15.value, "gemini-1.5-flash")
        self.assertEqual(GeminiModel.PRO_15.value, "gemini-1.5-pro")
        self.assertEqual(GeminiModel.PRO_VISION.value, "gemini-pro-vision")


if __name__ == '__main__':
    # 테스트 실행
    unittest.main(verbosity=2)
