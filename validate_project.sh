#!/bin/bash

# Project Validation Script
# 프로젝트 전체에서 금지 패턴을 검사하고 품질을 검증합니다.

set -e

echo "========================================="
echo "프로젝트 검증 시작: $(date)"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# 1. Mock/Fake 패턴 검색
echo -e "\n${YELLOW}[1/5] Mock/Fake 패턴 검사${NC}"
echo "----------------------------------------"

# Python 파일에서 mock 패턴 검색
MOCK_PATTERNS=$(grep -r "random\.\|faker\.\|Mock()\|from unittest.mock\|import mock" --include="*.py" --exclude-dir=tests --exclude-dir=test --exclude-dir=__pycache__ --exclude-dir=venv --exclude-dir=env . 2>/dev/null | grep -v "test_" || true)
if [ ! -z "$MOCK_PATTERNS" ]; then
    echo -e "${RED}❌ Mock 패턴 발견:${NC}"
    echo "$MOCK_PATTERNS" | head -20
    ((ERRORS++))
else
    echo -e "${GREEN}✅ Mock 패턴 없음${NC}"
fi

# 2. 중복/버전 파일 검사
echo -e "\n${YELLOW}[2/5] 중복/버전 파일 검사${NC}"
echo "----------------------------------------"

DUPLICATE_FILES=$(find . -type f \( -name "*_v2.py" -o -name "*_new.py" -o -name "*_backup.py" -o -name "*_old.py" -o -name "*_temp.py" \) 2>/dev/null | grep -v "__pycache__" || true)
if [ ! -z "$DUPLICATE_FILES" ]; then
    echo -e "${RED}❌ 중복/버전 파일 발견:${NC}"
    echo "$DUPLICATE_FILES"
    ((ERRORS++))
else
    echo -e "${GREEN}✅ 중복 파일 없음${NC}"
fi

# 3. 금지된 URL 패턴 검사
echo -e "\n${YELLOW}[3/5] 금지된 URL 패턴 검사${NC}"
echo "----------------------------------------"

FAKE_URLS=$(grep -r "example\.com\|test\.com\|localhost\.com\|dummy\.com" --include="*.py" --include="*.js" --include="*.jsx" --exclude-dir=tests --exclude-dir=test --exclude-dir=node_modules . 2>/dev/null || true)
if [ ! -z "$FAKE_URLS" ]; then
    echo -e "${YELLOW}⚠️  가짜 URL 패턴 발견:${NC}"
    echo "$FAKE_URLS" | head -10
    ((WARNINGS++))
else
    echo -e "${GREEN}✅ 가짜 URL 패턴 없음${NC}"
fi

# 4. 환경변수 파일 검사
echo -e "\n${YELLOW}[4/5] 환경변수 파일 검사${NC}"
echo "----------------------------------------"

ENV_FILES=$(find . -name ".env" 2>/dev/null | grep -v node_modules || true)
if [ ! -z "$ENV_FILES" ]; then
    echo -e "${YELLOW}⚠️  .env 파일 발견 (커밋 금지):${NC}"
    echo "$ENV_FILES"
    ((WARNINGS++))
fi

ENV_EXAMPLE=$(find . -name ".env.example" -o -name ".env.sample" 2>/dev/null | head -5 || true)
if [ ! -z "$ENV_EXAMPLE" ]; then
    echo -e "${GREEN}✅ .env.example 파일 존재${NC}"
else
    echo -e "${YELLOW}⚠️  .env.example 파일 없음${NC}"
fi

# 5. QA 설정 검증
echo -e "\n${YELLOW}[5/5] QA 설정 검증${NC}"
echo "----------------------------------------"

# Collector 서비스 QA 설정 확인
if [ -f "BACKEND-COLLECTOR-SERVICE/app/config.py" ]; then
    QA_CONFIG=$(grep -E "qa_domain_whitelist|qa_min_content_length|qa_expected_keywords" BACKEND-COLLECTOR-SERVICE/app/config.py 2>/dev/null || true)
    if [ ! -z "$QA_CONFIG" ]; then
        echo -e "${GREEN}✅ Collector QA 설정 구현됨${NC}"
    else
        echo -e "${YELLOW}⚠️  Collector QA 설정 없음${NC}"
        ((WARNINGS++))
    fi
fi

# CI/CD 파일 확인
if [ -f ".github/workflows/ci.yml" ]; then
    echo -e "${GREEN}✅ CI/CD 파이프라인 존재${NC}"
else
    echo -e "${RED}❌ CI/CD 파이프라인 없음${NC}"
    ((ERRORS++))
fi

# 결과 요약
echo "========================================="
echo -e "${YELLOW}검증 완료${NC}"
echo "========================================="
echo -e "오류: ${RED}$ERRORS${NC}"
echo -e "경고: ${YELLOW}$WARNINGS${NC}"

if [ $ERRORS -gt 0 ]; then
    echo -e "\n${RED}❌ 검증 실패: 오류를 수정하세요${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "\n${YELLOW}⚠️  경고 있음: 검토 필요${NC}"
    exit 0
else
    echo -e "\n${GREEN}✅ 모든 검증 통과${NC}"
    exit 0
fi
