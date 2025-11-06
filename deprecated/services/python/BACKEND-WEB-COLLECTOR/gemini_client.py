from __future__ import annotations
import json
import re
import requests
from typing import Any, Dict, List, Optional, Union
from enum import Enum


class GeminiModel(Enum):
    """Available Gemini models with their characteristics"""
    FLASH_15 = "gemini-1.5-flash"  # Fast, cost-effective
    PRO_15 = "gemini-1.5-pro"     # High accuracy
    VISION_15 = "gemini-1.5-pro-vision"  # Vision capabilities


class GeminiClient:
    """
    Gemini AI client optimized for pension sentiment analysis and web content processing.
    
    Features:
    - Multiple model support (Flash, Pro, Vision)
    - Pension-specific prompts and analysis
    - Structured JSON output parsing
    - Korean language support
    - Rate limiting and error handling
    """

    def __init__(self, api_key: str, model: str = GeminiModel.FLASH_15.value, timeout: int = 30):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
        })

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from Gemini response with fallback parsing"""
        # Try direct parse first
        try:
            return json.loads(text)
        except Exception:
            pass
        
        # Try to find JSON object in markdown code blocks
        json_pattern = r"```(?:json)?\s*(\{[\s\S]*?\})\s*```"
        match = re.search(json_pattern, text, re.IGNORECASE)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass
        
        # Try to find the first JSON object in the text
        json_obj_pattern = r"\{[\s\S]*\}"
        match = re.search(json_obj_pattern, text)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        
        raise ValueError("Failed to parse JSON from Gemini response")

    def _make_request(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> str:
        """Make request to Gemini API"""
        url = f"{self.base_url}/models/{self.model}:generateContent"
        
        # Convert messages to Gemini format
        contents = []
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 4096,
                "topP": 0.8,
                "topK": 40
            }
        }
        
        params = {"key": self.api_key}
        resp = self.session.post(url, json=payload, params=params, timeout=self.timeout)
        resp.raise_for_status()
        
        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected Gemini response format: {data}") from e

    def analyze_pension_content(self, content: str, url: str = "", additional_context: str = "") -> Dict[str, Any]:
        """
        Analyze web content for pension-related sentiment and information
        
        Returns structured analysis including:
        - sentiment (positive/negative/neutral)
        - confidence (0-1)
        - key_topics (list)
        - summary (string)
        - relevance_score (0-1)
        - entities (list of pension-related entities)
        """
        system_prompt = """You are an expert analyst specializing in pension and retirement policy sentiment analysis for South Korea.

Analyze the provided content and return STRICTLY a JSON object with these exact keys:
{
  "sentiment": "positive|negative|neutral",
  "confidence": 0.0-1.0,
  "relevance_score": 0.0-1.0,
  "key_topics": ["topic1", "topic2"],
  "summary": "brief summary in Korean",
  "entities": ["entity1", "entity2"],
  "pension_keywords": ["keyword1", "keyword2"],
  "policy_impact": "high|medium|low|none",
  "demographic_focus": "youth|middle_aged|elderly|general|unknown"
}

Focus on:
- Korean pension system (국민연금, 기초연금, 개인연금)
- Retirement policy changes
- Economic impact on retirees
- Public opinion and sentiment
- Government policy announcements
- Financial market impact on pensions

Return ONLY the JSON object, no additional text."""

        user_prompt = f"""Content URL: {url}
Additional Context: {additional_context}

Content to analyze:
{content[:4000]}"""  # Limit content to avoid token limits

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self._make_request(messages, temperature=0.1)
            return self._extract_json(response)
        except Exception as e:
            # Return default structure on error
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "relevance_score": 0.0,
                "key_topics": [],
                "summary": f"분석 오류: {str(e)}",
                "entities": [],
                "pension_keywords": [],
                "policy_impact": "none",
                "demographic_focus": "unknown"
            }

    def extract_structured_data(self, html_content: str, target_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from HTML using AI
        
        Args:
            html_content: Raw HTML content
            target_schema: Expected output schema
        
        Returns:
            Extracted structured data matching the schema
        """
        system_prompt = f"""You are a web scraping expert. Extract structured data from HTML content.

Return STRICTLY a JSON object matching this schema:
{json.dumps(target_schema, indent=2)}

Extract relevant information from the HTML and map it to the schema fields.
If a field cannot be found, use null or empty string as appropriate.
Focus on pension, retirement, and financial content if present."""

        user_prompt = f"""Extract data from this HTML content:

{html_content[:6000]}"""  # Limit HTML to avoid token limits

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self._make_request(messages, temperature=0.1)
            return self._extract_json(response)
        except Exception as e:
            # Return schema with empty/null values
            result = {}
            for key, value in target_schema.items():
                if isinstance(value, str):
                    result[key] = ""
                elif isinstance(value, list):
                    result[key] = []
                elif isinstance(value, dict):
                    result[key] = {}
                else:
                    result[key] = None
            return result

    def generate_search_queries(self, topic: str, count: int = 5) -> List[str]:
        """
        Generate diverse search queries for a pension-related topic
        
        Returns list of optimized search queries in Korean and English
        """
        system_prompt = """You are a search query optimization expert for pension and retirement topics.

Generate diverse, effective search queries that will find the most relevant and recent information.

Return STRICTLY a JSON object with this format:
{
  "queries": ["query1", "query2", "query3", ...]
}

Include both Korean and English queries. Focus on:
- Official government sources
- News articles
- Policy documents
- Public opinion
- Economic analysis"""

        user_prompt = f"""Generate {count} search queries for topic: {topic}

Target: South Korean pension system and retirement policies
Language mix: Korean (primary) + English (secondary)
Focus: Recent developments, policy changes, public sentiment"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self._make_request(messages, temperature=0.3)
            result = self._extract_json(response)
            return result.get("queries", [f"{topic} 국민연금", f"{topic} pension Korea"])
        except Exception:
            # Fallback queries
            return [
                f"{topic} 국민연금",
                f"{topic} 연금 정책",
                f"{topic} pension Korea",
                f"{topic} retirement policy",
                f"Korea pension {topic}"
            ][:count]

    def summarize_multiple_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Summarize and synthesize information from multiple sources
        
        Args:
            sources: List of source documents with title, url, content
        
        Returns:
            Comprehensive summary and analysis
        """
        system_prompt = """You are an expert analyst synthesizing pension-related information from multiple sources.

Analyze all sources and return STRICTLY a JSON object:
{
  "overall_sentiment": "positive|negative|neutral|mixed",
  "confidence": 0.0-1.0,
  "key_findings": ["finding1", "finding2"],
  "summary": "comprehensive summary in Korean",
  "source_analysis": [
    {
      "source": "source_url",
      "sentiment": "positive|negative|neutral",
      "reliability": 0.0-1.0,
      "key_points": ["point1", "point2"]
    }
  ],
  "trending_topics": ["topic1", "topic2"],
  "policy_implications": "analysis of policy impact",
  "recommendation": "actionable insights"
}"""

        sources_text = ""
        for i, source in enumerate(sources[:10]):  # Limit to 10 sources
            sources_text += f"\n\nSource {i+1}: {source.get('title', 'Unknown')}\nURL: {source.get('url', '')}\nContent: {source.get('content', '')[:1000]}"

        user_prompt = f"""Analyze these pension-related sources:{sources_text}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self._make_request(messages, temperature=0.2)
            return self._extract_json(response)
        except Exception as e:
            return {
                "overall_sentiment": "neutral",
                "confidence": 0.0,
                "key_findings": [],
                "summary": f"분석 오류: {str(e)}",
                "source_analysis": [],
                "trending_topics": [],
                "policy_implications": "분석할 수 없음",
                "recommendation": "데이터 재수집 필요"
            }