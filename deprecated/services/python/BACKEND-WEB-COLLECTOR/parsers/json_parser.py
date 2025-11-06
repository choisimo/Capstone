"""
범용 JSON 응답 파서
"""
import json
import orjson
from typing import Any, Dict, List, Optional, Union
from jsonschema import validate, ValidationError as JSONSchemaError
from .base_parser import BaseParser, ParseResult, ValidationError
import logging

logger = logging.getLogger(__name__)


class JSONResponseParser(BaseParser):
    """
    범용 JSON 응답 파서
    
    다양한 AI 모델의 JSON 응답을 파싱
    """
    
    def __init__(self, schema: Optional[Dict[str, Any]] = None):
        """
        초기화
        
        Args:
            schema: JSON Schema (검증용)
        """
        super().__init__()
        self.schema = schema
        self.strict_mode = False  # 엄격 모드
    
    def parse(self, response: str, strict: bool = False, **kwargs) -> ParseResult:
        """
        JSON 응답 파싱
        
        Args:
            response: JSON 응답 문자열
            strict: 엄격 모드 여부
            **kwargs: 추가 파라미터
        
        Returns:
            ParseResult 객체
        """
        self.strict_mode = strict
        
        try:
            # 다양한 방법으로 JSON 추출 시도
            json_data = None
            
            # 1. 직접 파싱 (가장 빠름)
            try:
                json_data = orjson.loads(response)
            except:
                try:
                    json_data = json.loads(response)
                except:
                    pass
            
            # 2. 베이스 클래스 메서드 사용
            if json_data is None:
                json_data = self.extract_json(response)
            
            # 3. 느슨한 파싱 시도
            if json_data is None and not strict:
                json_data = self._loose_json_parse(response)
            
            if json_data is not None:
                # 데이터 정규화
                normalized = self.normalize_data(json_data)
                
                # 스키마 검증
                if self.schema and strict:
                    if not self._validate_schema(normalized):
                        return ParseResult(
                            success=False,
                            errors=["Schema validation failed"],
                            metadata={"raw_data": normalized}
                        )
                
                # 일반 검증
                if self.validate(normalized):
                    self.update_statistics(True)
                    return ParseResult(
                        success=True,
                        data=normalized,
                        metadata={
                            "parser": "JSONResponseParser",
                            "strict_mode": strict
                        }
                    )
                else:
                    # 검증 실패하지만 데이터는 반환
                    if not strict:
                        return ParseResult(
                            success=True,
                            data=normalized,
                            warnings=["Validation warnings exist"],
                            metadata={"partial": True}
                        )
            
            # 파싱 실패
            self.update_statistics(False)
            return ParseResult(
                success=False,
                errors=["Failed to parse JSON"],
                metadata={"response_preview": response[:200]}
            )
            
        except Exception as e:
            logger.error(f"JSON parse error: {e}")
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
        if not isinstance(data, (dict, list)):
            return False
        
        if isinstance(data, dict):
            # 빈 딕셔너리 체크
            if not data:
                return False
            
            # 모든 값이 None인지 체크
            non_null = [v for v in data.values() if v is not None]
            if not non_null:
                return False
        
        elif isinstance(data, list):
            # 빈 리스트 체크
            if not data:
                return False
        
        return True
    
    def _validate_schema(self, data: Dict[str, Any]) -> bool:
        """
        JSON Schema 검증
        
        Args:
            data: 검증할 데이터
        
        Returns:
            검증 성공 여부
        """
        if not self.schema:
            return True
        
        try:
            validate(instance=data, schema=self.schema)
            return True
        except JSONSchemaError as e:
            logger.warning(f"Schema validation error: {e.message}")
            return False
    
    def _loose_json_parse(self, response: str) -> Optional[Dict[str, Any]]:
        """
        느슨한 JSON 파싱 (비표준 JSON 처리)
        
        Args:
            response: 응답 텍스트
        
        Returns:
            파싱된 데이터 또는 None
        """
        # JavaScript 스타일 객체 처리
        cleaned = response.strip()
        
        # 따옴표 없는 키 처리
        # {key: value} -> {"key": value}
        import re
        
        # 단순 키 처리 (영문자, 숫자, 언더스코어)
        pattern = r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:'
        cleaned = re.sub(pattern, r'\1"\2":', cleaned)
        
        # 싱글 쿼트를 더블 쿼트로 변환
        # 주의: 문자열 내부의 싱글 쿼트는 보존해야 함
        if cleaned.count("'") % 2 == 0:  # 짝수 개일 때만
            cleaned = cleaned.replace("'", '"')
        
        # True/False/None을 JSON 형식으로
        cleaned = cleaned.replace('True', 'true')
        cleaned = cleaned.replace('False', 'false')
        cleaned = cleaned.replace('None', 'null')
        
        # 다시 파싱 시도
        try:
            return json.loads(cleaned)
        except:
            pass
        
        # 마지막 시도: eval (위험하므로 제한적 사용)
        if self._is_safe_for_eval(cleaned):
            try:
                import ast
                result = ast.literal_eval(cleaned)
                if isinstance(result, (dict, list)):
                    return result
            except:
                pass
        
        return None
    
    def _is_safe_for_eval(self, text: str) -> bool:
        """
        eval 사용 안전성 체크
        
        Args:
            text: 검사할 텍스트
        
        Returns:
            안전 여부
        """
        # 위험한 키워드 체크
        dangerous = [
            '__', 'import', 'exec', 'eval', 'open',
            'file', 'input', 'compile', 'globals', 'locals'
        ]
        
        text_lower = text.lower()
        for keyword in dangerous:
            if keyword in text_lower:
                return False
        
        # 길이 제한
        if len(text) > 50000:  # 50KB 제한
            return False
        
        return True
    
    def merge_responses(self, responses: List[str]) -> ParseResult:
        """
        여러 JSON 응답 병합
        
        Args:
            responses: JSON 응답 리스트
        
        Returns:
            병합된 ParseResult
        """
        merged_data = {}
        all_errors = []
        all_warnings = []
        
        for response in responses:
            result = self.parse(response)
            if result.success and result.data:
                # 딕셔너리 병합
                if isinstance(result.data, dict):
                    merged_data.update(result.data)
                # 리스트는 확장
                elif isinstance(result.data, list):
                    if "items" not in merged_data:
                        merged_data["items"] = []
                    merged_data["items"].extend(result.data)
            
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        if merged_data:
            return ParseResult(
                success=True,
                data=merged_data,
                warnings=all_warnings,
                metadata={"merged": True, "count": len(responses)}
            )
        else:
            return ParseResult(
                success=False,
                errors=all_errors or ["No data to merge"],
                warnings=all_warnings
            )
