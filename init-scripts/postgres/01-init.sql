-- PostgreSQL 초기화 스크립트
-- 국민연금 감정분석 시스템

-- pgvector 확장 생성
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- 스키마 생성
CREATE SCHEMA IF NOT EXISTS pension;
CREATE SCHEMA IF NOT EXISTS osint;

-- 기본 테이블 생성
-- 데이터 소스
CREATE TABLE IF NOT EXISTS pension.data_sources (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 수집된 데이터
CREATE TABLE IF NOT EXISTS pension.collected_data (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    source_id UUID REFERENCES pension.data_sources(id),
    title TEXT,
    content TEXT NOT NULL,
    url VARCHAR(500),
    author VARCHAR(255),
    published_at TIMESTAMP,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- 감성 분석 결과
CREATE TABLE IF NOT EXISTS pension.sentiment_analysis (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    data_id UUID REFERENCES pension.collected_data(id),
    sentiment VARCHAR(20) NOT NULL,
    confidence FLOAT,
    aspects JSONB,
    keywords TEXT[],
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 페르소나 프로필
CREATE TABLE IF NOT EXISTS pension.user_personas (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_identifier VARCHAR(255) UNIQUE NOT NULL,
    platform VARCHAR(50),
    sentiment_profile JSONB,
    activity_metrics JSONB,
    influence_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 알림 규칙
CREATE TABLE IF NOT EXISTS pension.alert_rules (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    condition VARCHAR(50) NOT NULL,
    threshold_value FLOAT,
    target_metric VARCHAR(100),
    notification_channels JSONB,
    is_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 알림 로그
CREATE TABLE IF NOT EXISTS pension.alert_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    rule_id UUID REFERENCES pension.alert_rules(id),
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message TEXT,
    metadata JSONB,
    is_sent BOOLEAN DEFAULT false
);

-- OSINT 계획
CREATE TABLE IF NOT EXISTS osint.collection_plans (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    priority INTEGER DEFAULT 5,
    schedule JSONB,
    targets JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP
);

-- OSINT 태스크
CREATE TABLE IF NOT EXISTS osint.tasks (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    plan_id UUID REFERENCES osint.collection_plans(id),
    type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    payload JSONB,
    result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 인덱스 생성
CREATE INDEX idx_collected_data_source ON pension.collected_data(source_id);
CREATE INDEX idx_collected_data_published ON pension.collected_data(published_at DESC);
CREATE INDEX idx_sentiment_data ON pension.sentiment_analysis(data_id);
CREATE INDEX idx_sentiment_analyzed ON pension.sentiment_analysis(analyzed_at DESC);
CREATE INDEX idx_persona_user ON pension.user_personas(user_identifier);
CREATE INDEX idx_alert_rule ON pension.alert_logs(rule_id);
CREATE INDEX idx_task_plan ON osint.tasks(plan_id);
CREATE INDEX idx_task_status ON osint.tasks(status);

-- Full-text search 인덱스
CREATE INDEX idx_content_search ON pension.collected_data USING GIN(to_tsvector('korean', content));
CREATE INDEX idx_title_search ON pension.collected_data USING GIN(to_tsvector('korean', title));

-- 기본 데이터 소스 추가
INSERT INTO pension.data_sources (name, type, url) VALUES
    ('국민연금공단', 'official', 'https://www.nps.or.kr'),
    ('보건복지부', 'official', 'https://www.mohw.go.kr'),
    ('네이버 뉴스', 'news', 'https://news.naver.com'),
    ('다음 뉴스', 'news', 'https://news.daum.net'),
    ('클리앙', 'community', 'https://www.clien.net'),
    ('뽐뿌', 'community', 'https://www.ppomppu.co.kr'),
    ('구글 뉴스 RSS', 'rss', 'https://news.google.com/rss')
ON CONFLICT DO NOTHING;

-- 기본 알림 규칙 추가
INSERT INTO pension.alert_rules (name, condition, threshold_value, target_metric, notification_channels) VALUES
    ('부정 감성 급증', 'threshold', 0.7, 'negative_sentiment_ratio', '["email", "slack"]'),
    ('데이터 수집 중단', 'anomaly', 0, 'collection_rate', '["email"]'),
    ('키워드 급상승', 'pattern', 2.0, 'keyword_frequency_change', '["slack"]')
ON CONFLICT DO NOTHING;
