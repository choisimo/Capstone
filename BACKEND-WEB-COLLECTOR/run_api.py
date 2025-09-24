#!/usr/bin/env python
"""
API 서버 실행 스크립트
"""
import os
import sys
import uvicorn
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """메인 함수"""
    # 환경 변수 확인
    if not os.getenv("GEMINI_API_KEY"):
        print("⚠️  Warning: GEMINI_API_KEY not set")
        print("Please set environment variable or create .env file")
        print("Example: export GEMINI_API_KEY='your-api-key'")
        return
    
    # API 키 설정 (선택적)
    if not os.getenv("API_KEY"):
        os.environ["API_KEY"] = "default-api-key-for-development"
        print("ℹ️  Using default API key for development")
    
    print("🚀 Starting Hybrid Crawler API Server...")
    print("📚 Documentation: http://localhost:8000/docs")
    print("🔧 Health Check: http://localhost:8000/api/v1/system/health")
    print("=" * 60)
    
    # Uvicorn 서버 실행
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()
