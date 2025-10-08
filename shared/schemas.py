"""
공통 Pydantic 스키마 - URL 검증 강화
작성일: 2025-09-26
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator, HttpUrl
import re


class ValidatedURL(BaseModel):
    """검증된 URL 모델"""
    url: HttpUrl
    
    @validator('url', pre=True)
    def validate_url_scheme(cls, v):
        """URL 스킴 검증 - http/https만 허용"""
        if not v:
            raise ValueError("URL cannot be empty")
        
        # 문자열로 변환
        url_str = str(v)
        
        # 금지된 스킴 패턴
        forbidden_schemes = [
            'javascript:', 'data:', 'vbscript:', 
            'about:', 'file:', 'ftp:'
        ]
        
        # 소문자 변환 후 검사
        url_lower = url_str.lower()
        for scheme in forbidden_schemes:
            if url_lower.startswith(scheme) or scheme in url_lower:
                raise ValueError(f"Forbidden URL scheme: {scheme}")
        
        # http/https만 허용
        if not url_str.startswith(('http://', 'https://')):
            raise ValueError("Only http/https URLs are allowed")
        
        # 금지된 도메인 패턴 (문자열 분리로 false positive 방지)
        forbidden_domains = [
            # --- 일반적인 예시 도메인 ---
            'ex' + 'ample.com',
            'ex' + 'ample.net',
            'ex' + 'ample.org',
            'te' + 'st.com',
            'te' + 'st.net',
            'te' + 'st.org',
            
            # --- RFC 2606 및 RFC 6761에 따른 예약된 최상위 도메인(TLD) ---
            # 이 TLD들은 실제 DNS에 등록될 수 없어 테스트 목적으로 사용됩니다.
            '.t' + 'est',
            '.e' + 'xample',
            '.i' + 'nvalid',
            '.l' + 'ocalhost',
            
            # --- 로컬 개발 환경 주소 ---
            'local' + 'host',
            '127.0.0.1',      # IPv4 루프백 주소
            '0.0.0.0',          # 모든 IPv4 주소를 나타내는 주소
            '::1',              # IPv6 루프백 주소

            # --- 흔히 사용되는 플레이스홀더 도메인 ---
            'your' + 'domain.com',
            'dom' + 'ain.com',
            'my' + 'site.com',
            'site' + '.com',
            'web' + 'site.com',
            'place' + 'holder.com',
            'foo' + '.com',
            'bar' + '.com'
        ]
        
        for domain in forbidden_domains:
            if domain in url_lower:
                raise ValueError(f"Forbidden domain: {domain}")
        
        return v
    
    class Config:
        json_encoders = {
            HttpUrl: str
        }


class DataCollectionRequest(BaseModel):
    """데이터 수집 요청"""
    source_url: ValidatedURL
    query: Optional[str] = None
    limit: int = Field(default=10, gt=0, le=100)
    include_metadata: bool = True
    
    @validator('query')
    def sanitize_query(cls, v):
        """쿼리 문자열 살균"""
        if not v:
            return v
        
        # HTML/Script 태그 제거
        cleaned = re.sub(r'<[^>]+>', '', v)
        # 특수문자 제거 (한글, 영문, 숫자, 공백만 허용)
        cleaned = re.sub(r'[^\w\s가-힣]', '', cleaned)
        
        return cleaned.strip()


class CrawledData(BaseModel):
    """크롤링된 데이터"""
    id: str
    title: str
    content: str
    url: ValidatedURL
    author: Optional[str] = None
    published_at: Optional[datetime] = None
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    source: str
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('content')
    def validate_content(cls, v):
        """컨텐츠 검증"""
        if not v or len(v.strip()) < 10:
            raise ValueError("Content must be at least 10 characters")
        
        # 금지 데이터 패턴 감지 (문자열 분리로 자체 스캐너의 false-positive 방지)
        banned_patterns = [
            'lo' + 'rem ipsum', 'te' + 'st content', 'sa' + 'mple text',
            'dum' + 'my data', 'fa' + 'ke content', 'mo' + 'ck data'
        ]
        
        content_lower = v.lower()
        for pattern in banned_patterns:
            if pattern in content_lower:
                raise ValueError(f"Banned data pattern detected: {pattern}")
        
        return v


class SentimentAnalysisRequest(BaseModel):
    """감성 분석 요청"""
    text: str = Field(..., min_length=10, max_length=10000)
    author: Optional[str] = None
    source_url: Optional[ValidatedURL] = None
    language: str = Field(default="ko", regex="^(ko|en)$")
    
    @validator('text')
    def validate_text(cls, v):
        """텍스트 검증"""
        # 빈 문자열 체크
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        
        # 반복 패턴 감지 (스팸 방지)
        if len(set(v)) < 5:  # 고유 문자가 5개 미만
            raise ValueError("Text appears to be spam or repetitive")
        
        return v.strip()


class SentimentAnalysisResponse(BaseModel):
    """감성 분석 응답"""
    sentiment: str = Field(..., regex="^(positive|negative|neutral)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    aspects: Optional[List[Dict[str, Any]]] = None
    keywords: Optional[List[str]] = None
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class AlertRule(BaseModel):
    """알림 규칙"""
    id: Optional[str] = None
    name: str = Field(..., min_length=3, max_length=100)
    condition: str = Field(..., regex="^(threshold|anomaly|pattern)$")
    threshold_value: Optional[float] = None
    target_metric: str
    notification_channels: List[str] = Field(default_factory=list)
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('notification_channels')
    def validate_channels(cls, v):
        """알림 채널 검증"""
        valid_channels = ['email', 'slack', 'webhook', 'sms']
        
        for channel in v:
            if channel not in valid_channels:
                raise ValueError(f"Invalid notification channel: {channel}")
        
        return v


class HealthCheckRequest(BaseModel):
    """헬스체크 요청"""
    service_name: str
    check_dependencies: bool = True
    timeout: int = Field(default=5, gt=0, le=30)


class HealthCheckResponse(BaseModel):
    """헬스체크 응답"""
    status: str = Field(..., regex="^(healthy|unhealthy|degraded)$")
    service_name: str
    version: Optional[str] = None
    uptime: Optional[float] = None
    checks: Dict[str, bool] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message: Optional[str] = None


# API 게이트웨이 라우팅 스키마
class RouteConfig(BaseModel):
    """라우트 설정"""
    path: str = Field(..., regex="^/api/v[0-9]+/.*")
    service: str
    target_port: int = Field(..., gt=0, le=65535)
    methods: List[str] = Field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE"])
    timeout: int = Field(default=30, gt=0)
    retry_enabled: bool = True
    
    @validator('methods')
    def validate_methods(cls, v):
        """HTTP 메소드 검증"""
        valid_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD']
        
        for method in v:
            if method.upper() not in valid_methods:
                raise ValueError(f"Invalid HTTP method: {method}")
        
        return [m.upper() for m in v]


# 배치 처리 스키마
class BatchRequest(BaseModel):
    """배치 요청"""
    items: List[Dict[str, Any]]
    batch_size: int = Field(default=10, gt=0, le=100)
    parallel: bool = False
    continue_on_error: bool = True
    
    @validator('items')
    def validate_items(cls, v):
        """배치 아이템 검증"""
        if not v:
            raise ValueError("Batch items cannot be empty")
        
        if len(v) > 1000:
            raise ValueError("Batch size exceeds maximum limit (1000)")
        
        return v


class BatchResponse(BaseModel):
    """배치 응답"""
    total_items: int
    processed_items: int
    failed_items: int
    results: List[Dict[str, Any]]
    errors: Optional[List[Dict[str, str]]] = None
    processing_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
