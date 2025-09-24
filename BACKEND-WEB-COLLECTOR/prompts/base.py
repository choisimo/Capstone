"""
프롬프트 템플릿 베이스 클래스
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import json
from datetime import datetime


class PromptMetadata(BaseModel):
    """프롬프트 메타데이터"""
    version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    language: str = Field(default="ko")
    domain: str = Field(default="pension")
    tags: List[str] = Field(default_factory=list)


class BasePromptTemplate(ABC):
    """
    프롬프트 템플릿 베이스 클래스
    
    모든 프롬프트 템플릿의 기본 인터페이스 제공
    """
    
    def __init__(self):
        self.metadata = PromptMetadata()
        self.template_cache = {}
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """시스템 프롬프트 반환"""
        pass
    
    @abstractmethod
    def get_user_prompt(self, content: str, **kwargs) -> str:
        """사용자 프롬프트 생성"""
        pass
    
    @abstractmethod
    def get_output_schema(self) -> Dict[str, Any]:
        """예상 출력 스키마 반환"""
        pass
    
    def format_prompt(
        self, 
        content: str,
        include_system: bool = True,
        **kwargs
    ) -> str:
        """
        완전한 프롬프트 생성
        
        Args:
            content: 분석할 콘텐츠
            include_system: 시스템 프롬프트 포함 여부
            **kwargs: 추가 파라미터
        
        Returns:
            포맷된 프롬프트 문자열
        """
        prompt_parts = []
        
        if include_system:
            system_prompt = self.get_system_prompt()
            if system_prompt:
                prompt_parts.append(f"시스템 지시사항:\n{system_prompt}\n")
        
        user_prompt = self.get_user_prompt(content, **kwargs)
        prompt_parts.append(f"사용자 요청:\n{user_prompt}")
        
        # 출력 형식 명시
        output_schema = self.get_output_schema()
        if output_schema:
            prompt_parts.append(f"\n\n출력 형식 (JSON):\n{json.dumps(output_schema, ensure_ascii=False, indent=2)}")
        
        return "\n".join(prompt_parts)
    
    def validate_response(self, response: Dict[str, Any]) -> bool:
        """
        응답 검증
        
        Args:
            response: AI 응답 딕셔너리
        
        Returns:
            검증 성공 여부
        """
        schema = self.get_output_schema()
        if not schema:
            return True
        
        # 기본 검증: 필수 키 확인
        for key in schema.keys():
            if key not in response:
                return False
        
        return True
    
    def get_examples(self) -> List[Dict[str, str]]:
        """
        예시 입출력 반환
        
        Returns:
            예시 리스트
        """
        return []
    
    def get_version(self) -> str:
        """템플릿 버전 반환"""
        return self.metadata.version
    
    def update_metadata(self, **kwargs):
        """메타데이터 업데이트"""
        for key, value in kwargs.items():
            if hasattr(self.metadata, key):
                setattr(self.metadata, key, value)
        self.metadata.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """템플릿을 딕셔너리로 변환"""
        return {
            "class": self.__class__.__name__,
            "metadata": self.metadata.dict(),
            "system_prompt": self.get_system_prompt(),
            "output_schema": self.get_output_schema(),
            "examples": self.get_examples()
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(version={self.metadata.version}, domain={self.metadata.domain})"
