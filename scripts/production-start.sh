#!/bin/bash

# 국민연금 감정분석 시스템 - 프로덕션 시작 스크립트
# 단일 명령으로 전체 시스템 시작

set -e

echo "=================================================="
echo "국민연금 감정분석 시스템 - Production 시작"
echo "=================================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 환경 파일 체크
if [ ! -f ".env.production" ]; then
    echo -e "${YELLOW}⚠️  .env.production 파일이 없습니다. 기본값을 사용합니다.${NC}"
    cp .env.production.example .env.production 2>/dev/null || true
fi

# 환경 변수 로드
export $(cat .env.production | grep -v '^#' | xargs)

# Docker 체크
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker가 설치되어 있지 않습니다.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose가 설치되어 있지 않습니다.${NC}"
    exit 1
fi

echo -e "${BLUE}🔍 시스템 요구사항 체크...${NC}"
echo "  • Docker: $(docker --version)"
echo "  • Docker Compose: $(docker-compose --version)"

# 기존 컨테이너 정리
echo -e "\n${BLUE}🧹 기존 컨테이너 정리...${NC}"
docker-compose -f docker-compose.production.yml down 2>/dev/null || true

# 볼륨 초기화 (선택적)
if [ "$1" == "--clean" ]; then
    echo -e "${YELLOW}⚠️  볼륨 초기화 중...${NC}"
    docker-compose -f docker-compose.production.yml down -v
fi

# 필요한 디렉토리 생성
echo -e "\n${BLUE}📁 디렉토리 구조 생성...${NC}"
mkdir -p init-scripts/{postgres,mongo}
mkdir -p monitoring/grafana/provisioning/{dashboards,datasources}
mkdir -p logs
mkdir -p shared

# 이미지 빌드
echo -e "\n${BLUE}🔨 Docker 이미지 빌드...${NC}"
docker-compose -f docker-compose.production.yml build --parallel

# 인프라 서비스 시작
echo -e "\n${BLUE}🚀 인프라 서비스 시작...${NC}"
docker-compose -f docker-compose.production.yml up -d postgres redis mongo

# 인프라 준비 대기
echo -e "${YELLOW}⏳ 데이터베이스 초기화 대기 (30초)...${NC}"
sleep 30

# 헬스체크
echo -e "\n${BLUE}🏥 인프라 헬스체크...${NC}"
docker-compose -f docker-compose.production.yml ps postgres redis mongo

# 마이크로서비스 시작
echo -e "\n${BLUE}🚀 마이크로서비스 시작...${NC}"
docker-compose -f docker-compose.production.yml up -d \
    api-gateway \
    analysis-service \
    collector-service \
    absa-service \
    alert-service \
    osint-orchestrator \
    osint-planning \
    osint-source

# 서비스 준비 대기
echo -e "${YELLOW}⏳ 서비스 초기화 대기 (30초)...${NC}"
sleep 30

# 프론트엔드 시작
echo -e "\n${BLUE}🎨 프론트엔드 시작...${NC}"
docker-compose -f docker-compose.production.yml up -d frontend

# 모니터링 시작 (옵션)
if [ "$2" == "--with-monitoring" ]; then
    echo -e "\n${BLUE}📊 모니터링 서비스 시작...${NC}"
    docker-compose -f docker-compose.production.yml up -d prometheus grafana
fi

# 전체 상태 확인
echo -e "\n${BLUE}📋 서비스 상태 확인...${NC}"
docker-compose -f docker-compose.production.yml ps

# 헬스체크 실행
echo -e "\n${BLUE}🏥 헬스체크 실행...${NC}"
./check-health.sh 2>/dev/null || {
    echo -e "${YELLOW}헬스체크 스크립트가 없습니다. 수동 확인이 필요합니다.${NC}"
}

echo -e "\n${GREEN}✅ 시스템 시작 완료!${NC}"
echo ""
echo "=================================================="
echo "📍 서비스 접속 정보"
echo "=================================================="
echo "  • Frontend:          http://localhost:3000"
echo "  • API Gateway:       http://localhost:8000"
echo "  • API Docs:          http://localhost:8000/docs"
echo "  • Prometheus:        http://localhost:9090"
echo "  • Grafana:           http://localhost:3001 (admin/Gr@fana2025)"
echo ""
echo "  • Analysis Service:  http://localhost:8001"
echo "  • Collector Service: http://localhost:8002"
echo "  • ABSA Service:      http://localhost:8003"
echo "  • Alert Service:     http://localhost:8004"
echo ""
echo "=================================================="
echo ""
echo "💡 팁:"
echo "  • 로그 확인: docker-compose -f docker-compose.production.yml logs -f <service-name>"
echo "  • 서비스 재시작: docker-compose -f docker-compose.production.yml restart <service-name>"
echo "  • 전체 중지: docker-compose -f docker-compose.production.yml down"
echo "  • 전체 제거: docker-compose -f docker-compose.production.yml down -v"
echo ""
