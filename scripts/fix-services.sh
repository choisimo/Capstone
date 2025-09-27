#!/bin/bash

# 프로덕션 서비스 수정 스크립트

echo "🔧 프로덕션 서비스 DATABASE_URL 수정 중..."

# 1. 모든 서비스 중지
echo "⏹️  서비스 중지..."
docker-compose -f docker-compose.production.yml down

# 2. docker-compose.yml 백업
echo "📋 설정 백업..."
cp docker-compose.production.yml docker-compose.production.yml.backup

# 3. DATABASE_URL 직접 수정 (URL-encoded 버전)
echo "✏️  DATABASE_URL 수정..."
cat > /tmp/fix-database-urls.py << 'EOF'
import sys

with open('docker-compose.production.yml', 'r') as f:
    content = f.read()

# PostgreSQL DATABASE_URL 수정
content = content.replace(
    'DATABASE_URL: postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD_URLENC:-StrongP%40ssw0rd2025}@postgres:5432/${POSTGRES_DB:-pension_sentiment}',
    'DATABASE_URL: postgresql://postgres:StrongP%40ssw0rd2025@postgres:5432/pension_sentiment'
)

# MongoDB URL 수정
content = content.replace(
    'MONGO_URL: mongodb://${MONGO_ROOT_USERNAME:-admin}:${MONGO_ROOT_PASSWORD_URLENC:-M0ngoP%40ss2025}@mongo:27017/osint_data?authSource=admin',
    'MONGO_URL: mongodb://admin:M0ngoP%40ss2025@mongo:27017/osint_data?authSource=admin'
)

with open('docker-compose.production.yml', 'w') as f:
    f.write(content)

print("✅ DATABASE URLs fixed with URL-encoded passwords")
EOF

python3 /tmp/fix-database-urls.py

# 4. 인프라 서비스 시작
echo "🚀 인프라 서비스 시작..."
docker-compose -f docker-compose.production.yml up -d postgres redis mongo

# 5. 인프라 준비 대기
echo "⏳ 인프라 준비 대기 (30초)..."
sleep 30

# 6. 모든 마이크로서비스 시작
echo "🚀 마이크로서비스 시작..."
docker-compose -f docker-compose.production.yml up -d

# 7. 서비스 안정화 대기
echo "⏳ 서비스 안정화 대기 (60초)..."
sleep 60

# 8. 헬스체크 실행
echo "🏥 헬스체크 실행..."
./check-health.sh

echo "✅ 완료!"
