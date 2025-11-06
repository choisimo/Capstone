"""
베이스 파서 클래스 및 에러 정의
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ValidationError as PydanticValidationError
import json
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ParserError(Exception):
    """파서 관련 기본 에러"""
    pass


class ValidationError(ParserError):
    """데이터 검증 실패 에러"""
    pass


class ParseResult(BaseModel):
    """파싱 결과 모델"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = []
    warnings: List[str] = []
    metadata: Dict[str, Any] = {}
    timestamp: datetime = datetime.utcnow()


class BaseParser(ABC):
    """
    AI 응답 파서 베이스 클래스
    
    모든 파서의 공통 인터페이스 제공
    """
    
    def __init__(self):
        self.parse_count = 0
        self.error_count = 0
        self.success_rate = 0.0
    
    @abstractmethod
    def parse(self, response: str, **kwargs) -> ParseResult:
        """
        응답 파싱 메인 메서드
        
        Args:
            response: 파싱할 응답 문자열
            **kwargs: 추가 파라미터
        
        Returns:
            ParseResult 객체
        """
        pass
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        파싱된 데이터 검증
        
        Args:
            data: 검증할 데이터
        
        Returns:
            검증 성공 여부
        """
        pass
    
    def extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """
        텍스트에서 JSON 추출 (공통 유틸리티)
        
        Args:
            text: JSON이 포함된 텍스트
        
        Returns:
            추출된 JSON 딕셔너리 또는 None
        """
        # 직접 JSON 파싱 시도
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 마크다운 코드 블록에서 추출
        patterns = [
            r"```(?:json)?\s*\n?({[\s\S]*?})\s*\n?```",  # ```json 또는 ``` 블록
            r"```(?:json)?\s*\n?(\[[\s\S]*?\])\s*\n?```",  # 배열 형태
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue
        
        # 텍스트에서 첫 번째 JSON 객체 찾기
        json_patterns = [
            r"(\{[^{}]*\{[^{}]*\}[^{}]*\})",  # 중첩된 객체
            r"(\{[^{}]*\})",  # 단순 객체
            r"(\[[^\[\]]*\])",  # 배열
        ]
        
        for pattern in json_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def clean_text(self, text: str) -> str:
        """
        텍스트 정제
        
        Args:
            text: 정제할 텍스트
        
        Returns:
            정제된 텍스트
        """
        # 불필요한 공백 제거
        text = re.sub(r'\s+', ' ', text)
        # 제어 문자 제거
        text = re.sub(r'[\x00-\x1F\x7F-\x9F]', '', text)
        # 앞뒤 공백 제거
        return text.strip()
    
    def extract_key_value_pairs(self, text: str) -> Dict[str, str]:
        """
        텍스트에서 키-값 쌍 추출
        
        Args:
            text: 키-값 쌍이 포함된 텍스트
        
        Returns:
            추출된 키-값 딕셔너리
        """
        pairs = {}
        
        # 패턴: "key: value" 또는 "key = value"
        patterns = [
            r"([^:=\n]+)[:=]\s*([^\n]+)",
            r"- ([^:]+):\s*([^\n]+)",  # 리스트 형식
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                key = self.clean_text(match.group(1))
                value = self.clean_text(match.group(2))
                if key and value:
                    pairs[key] = value
        
        return pairs
    
    def normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        데이터 정규화
        
        Args:
            data: 정규화할 데이터
        
        Returns:
            정규화된 데이터
        """
        normalized = {}
        
        for key, value in data.items():
            # 키 정규화 (snake_case)
            normalized_key = re.sub(r'([A-Z])', r'_\1', key).lower().strip('_')
            
            # 값 정규화
            if isinstance(value, str):
                # 문자열 정제
                normalized[normalized_key] = self.clean_text(value)
            elif isinstance(value, dict):
                # 재귀적 정규화
                normalized[normalized_key] = self.normalize_data(value)
            elif isinstance(value, list):
                # 리스트 요소 정규화
                normalized[normalized_key] = [
                    self.normalize_data(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                normalized[normalized_key] = value
        
        return normalized
    
    def update_statistics(self, success: bool):
        """
        파싱 통계 업데이트
        
        Args:
            success: 파싱 성공 여부
        """
        self.parse_count += 1
        if not success:
            self.error_count += 1
        
        if self.parse_count > 0:
            self.success_rate = (self.parse_count - self.error_count) / self.parse_count
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        파싱 통계 반환
        
        Returns:
            통계 딕셔너리
        """
        return {
            "total_parses": self.parse_count,
            "errors": self.error_count,
            "success_rate": self.success_rate,
            "success_count": self.parse_count - self.error_count
        }
    
    def reset_statistics(self):
        """통계 초기화"""
        self.parse_count = 0
        self.error_count = 0
        self.success_rate = 0.0
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(success_rate={self.success_rate:.2%})"
