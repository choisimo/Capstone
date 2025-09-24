"""
구조화된 데이터 파서
"""
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, ValidationError as PydanticError, create_model
from .base_parser import BaseParser, ParseResult, ValidationError
import logging
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


class StructuredDataParser(BaseParser):
    """
    Pydantic 모델 기반 구조화 데이터 파서
    
    타입 안전성과 자동 검증을 제공
    """
    
    def __init__(self, model: Optional[Type[BaseModel]] = None):
        """
        초기화
        
        Args:
            model: Pydantic 모델 클래스
        """
        super().__init__()
        self.model = model
        self.dynamic_models = {}  # 동적 생성 모델 캐시
    
    def parse(
        self, 
        response: str, 
        model: Optional[Type[BaseModel]] = None,
        **kwargs
    ) -> ParseResult:
        """
        구조화된 데이터 파싱
        
        Args:
            response: 응답 문자열
            model: 사용할 Pydantic 모델
            **kwargs: 추가 파라미터
        
        Returns:
            ParseResult 객체
        """
        # 모델 선택
        target_model = model or self.model
        
        try:
            # JSON 추출
            json_data = self.extract_json(response)
            if not json_data:
                # 텍스트에서 구조 추출 시도
                json_data = self._extract_structure(response)
            
            if json_data:
                # 동적 모델 생성 (필요시)
                if not target_model:
                    target_model = self._create_dynamic_model(json_data)
                
                # Pydantic 모델로 파싱
                if target_model:
                    try:
                        parsed_model = target_model(**json_data)
                        parsed_data = parsed_model.dict()
                        
                        self.update_statistics(True)
                        return ParseResult(
                            success=True,
                            data=parsed_data,
                            metadata={
                                "model": target_model.__name__,
                                "validated": True
                            }
                        )
                    except PydanticError as e:
                        # 부분 파싱 시도
                        partial_data = self._partial_parse(json_data, target_model)
                        if partial_data:
                            return ParseResult(
                                success=True,
                                data=partial_data,
                                warnings=[f"Partial parse: {str(e)}"],
                                metadata={"partial": True}
                            )
                else:
                    # 모델 없이 기본 파싱
                    normalized = self.normalize_data(json_data)
                    if self.validate(normalized):
                        return ParseResult(
                            success=True,
                            data=normalized,
                            metadata={"model": "none"}
                        )
            
            # 파싱 실패
            self.update_statistics(False)
            return ParseResult(
                success=False,
                errors=["Failed to parse structured data"],
                metadata={"response_preview": response[:200]}
            )
            
        except Exception as e:
            logger.error(f"Structured parse error: {e}")
            self.update_statistics(False)
            return ParseResult(
                success=False,
                errors=[str(e)],
                metadata={"exception": type(e).__name__}
            )
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        데이터 검증
        
        Args:
            data: 검증할 데이터
        
        Returns:
            검증 성공 여부
        """
        if not data:
            return False
        
        # 모델이 있으면 모델 검증
        if self.model:
            try:
                self.model(**data)
                return True
            except PydanticError:
                return False
        
        # 기본 검증
        return super().validate(data)
    
    def _extract_structure(self, text: str) -> Optional[Dict[str, Any]]:
        """
        텍스트에서 구조 추출
        
        Args:
            text: 텍스트
        
        Returns:
            추출된 구조 또는 None
        """
        import re
        
        structure = {}
        
        # 패턴 기반 추출
        patterns = {
            'sentiment': r'(?:sentiment|감성)[:\s]*([가-힣a-zA-Z]+)',
            'score': r'(?:score|점수)[:\s]*([-\d.]+)',
            'confidence': r'(?:confidence|신뢰도)[:\s]*([\d.]+)',
            'date': r'(\d{4}[-/]\d{2}[-/]\d{2})',
            'percentage': r'(\d+(?:\.\d+)?)[%％]',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1)
                # 타입 변환
                if key in ['score', 'confidence']:
                    try:
                        value = float(value)
                    except:
                        pass
                structure[key] = value
        
        # 리스트 항목 추출
        list_pattern = r'[-•*]\s*(.+)'
        list_matches = re.findall(list_pattern, text)
        if list_matches:
            structure['items'] = list_matches
        
        return structure if structure else None
    
    def _create_dynamic_model(self, data: Dict[str, Any]) -> Type[BaseModel]:
        """
        데이터 구조에 맞는 동적 Pydantic 모델 생성
        
        Args:
            data: 데이터 딕셔너리
        
        Returns:
            동적 생성된 모델 클래스
        """
        # 캐시 키 생성
        cache_key = frozenset(data.keys())
        
        # 캐시에서 확인
        if cache_key in self.dynamic_models:
            return self.dynamic_models[cache_key]
        
        # 필드 타입 추론
        fields = {}
        for key, value in data.items():
            field_type = self._infer_type(value)
            fields[key] = (field_type, None)  # (type, default)
        
        # 동적 모델 생성
        model = create_model(
            'DynamicModel',
            **fields
        )
        
        # 캐시 저장
        self.dynamic_models[cache_key] = model
        
        return model
    
    def _infer_type(self, value: Any) -> type:
        """
        값으로부터 타입 추론
        
        Args:
            value: 값
        
        Returns:
            추론된 타입
        """
        if value is None:
            return Optional[Any]
        elif isinstance(value, bool):
            return bool
        elif isinstance(value, int):
            return int
        elif isinstance(value, float):
            return float
        elif isinstance(value, str):
            return str
        elif isinstance(value, list):
            if value and len(value) > 0:
                item_type = self._infer_type(value[0])
                return List[item_type]
            return List[Any]
        elif isinstance(value, dict):
            return Dict[str, Any]
        else:
            return Any
    
    def _partial_parse(
        self, 
        data: Dict[str, Any], 
        model: Type[BaseModel]
    ) -> Optional[Dict[str, Any]]:
        """
        부분 파싱 (선택적 필드만)
        
        Args:
            data: 원본 데이터
            model: Pydantic 모델
        
        Returns:
            부분 파싱 결과 또는 None
        """
        partial_data = {}
        
        # 모델 필드 확인
        for field_name, field in model.__fields__.items():
            if field_name in data:
                value = data[field_name]
                # 필수 필드가 아니거나 값이 유효하면 포함
                if not field.required or value is not None:
                    partial_data[field_name] = value
            elif not field.required:
                # 선택적 필드는 기본값 사용
                partial_data[field_name] = field.default
        
        if partial_data:
            try:
                # 검증 시도
                model(**partial_data)
                return partial_data
            except PydanticError:
                # 더 느슨한 파싱
                return {k: v for k, v in partial_data.items() if v is not None}
        
        return None
    
    def create_model_from_schema(
        self, 
        schema: Dict[str, Any],
        name: str = "GeneratedModel"
    ) -> Type[BaseModel]:
        """
        스키마에서 Pydantic 모델 생성
        
        Args:
            schema: 필드 정의 스키마
            name: 모델 이름
        
        Returns:
            생성된 모델 클래스
        """
        fields = {}
        
        for field_name, field_def in schema.items():
            if isinstance(field_def, dict):
                field_type = field_def.get('type', Any)
                default = field_def.get('default', ...)
                description = field_def.get('description', '')
                
                # 타입 매핑
                type_map = {
                    'string': str,
                    'integer': int,
                    'float': float,
                    'boolean': bool,
                    'array': List[Any],
                    'object': Dict[str, Any]
                }
                
                if isinstance(field_type, str):
                    field_type = type_map.get(field_type, Any)
                
                fields[field_name] = (field_type, default)
            else:
                # 단순 타입
                fields[field_name] = (field_def, None)
        
        return create_model(name, **fields)
    
    def to_json_schema(self, model: Optional[Type[BaseModel]] = None) -> Dict[str, Any]:
        """
        Pydantic 모델을 JSON Schema로 변환
        
        Args:
            model: Pydantic 모델
        
        Returns:
            JSON Schema
        """
        target_model = model or self.model
        if not target_model:
            return {}
        
        return target_model.schema()
