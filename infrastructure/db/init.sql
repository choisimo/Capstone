-- Unified Database Initialization Script
-- Merged from: init-scripts/postgres/01-init.sql and database/init-osint.sql

-- =====================================================
-- EXTENSIONS
-- =====================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =====================================================
-- SCHEMAS
-- =====================================================
CREATE SCHEMA IF NOT EXISTS pension;
CREATE SCHEMA IF NOT EXISTS osint;

-- =====================================================
-- PENSION SCHEMA (Domain Specific Data)
-- =====================================================

-- Data Sources
CREATE TABLE IF NOT EXISTS pension.data_sources (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    url VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Collected Data
CREATE TABLE IF NOT EXISTS pension.collected_data (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    source_id UUID REFERENCES pension.data_sources(id),
    title TEXT,
    content TEXT NOT NULL,
    url VARCHAR(500),
    author VARCHAR(255),
    published_at TIMESTAMP WITH TIME ZONE,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

-- Sentiment Analysis Results
CREATE TABLE IF NOT EXISTS pension.sentiment_analysis (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    data_id UUID REFERENCES pension.collected_data(id),
    sentiment VARCHAR(20) NOT NULL, -- positive, negative, neutral
    sentiment_score DECIMAL(3,2), -- -1.0 to 1.0
    confidence FLOAT,
    aspects JSONB DEFAULT '{}',
    keywords TEXT[],
    model_version VARCHAR(50),
    analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Personas
CREATE TABLE IF NOT EXISTS pension.user_personas (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_identifier VARCHAR(255) UNIQUE NOT NULL,
    platform VARCHAR(50),
    sentiment_profile JSONB DEFAULT '{}',
    activity_metrics JSONB DEFAULT '{}',
    influence_score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Alert Rules
CREATE TABLE IF NOT EXISTS pension.alert_rules (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    condition VARCHAR(50) NOT NULL,
    threshold_value FLOAT,
    target_metric VARCHAR(100),
    notification_channels JSONB DEFAULT '[]',
    is_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Alert Logs
CREATE TABLE IF NOT EXISTS pension.alert_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    rule_id UUID REFERENCES pension.alert_rules(id),
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    message TEXT,
    metadata JSONB DEFAULT '{}',
    is_sent BOOLEAN DEFAULT false
);

-- =====================================================
-- OSINT SCHEMA (Collection & Processing Infrastructure)
-- =====================================================

-- Collection Plans (High level strategy)
CREATE TABLE IF NOT EXISTS osint.collection_plans (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    priority INTEGER DEFAULT 5,
    schedule JSONB DEFAULT '{}',
    targets JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    executed_at TIMESTAMP WITH TIME ZONE
);

-- Keywords for OSINT planning
CREATE TABLE IF NOT EXISTS osint.keywords (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword VARCHAR(255) NOT NULL,
    keyword_type VARCHAR(50) NOT NULL CHECK (keyword_type IN ('seed', 'expanded', 'alias')),
    expansion_method VARCHAR(100),
    parent_keyword_id UUID REFERENCES osint.keywords(id) ON DELETE SET NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.5,
    language VARCHAR(10) DEFAULT 'ko',
    domain VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'archived')),
    usage_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Keyword Co-occurrences
CREATE TABLE IF NOT EXISTS osint.keyword_cooccurrences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword1_id UUID NOT NULL REFERENCES osint.keywords(id) ON DELETE CASCADE,
    keyword2_id UUID NOT NULL REFERENCES osint.keywords(id) ON DELETE CASCADE,
    frequency INTEGER DEFAULT 1,
    context VARCHAR(500),
    confidence_score DECIMAL(3,2) DEFAULT 0.5,
    source VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyword1_id, keyword2_id)
);

-- Sources Registry (More detailed than pension.data_sources)
CREATE TABLE IF NOT EXISTS osint.sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    url VARCHAR(2048) NOT NULL UNIQUE,
    host VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('news', 'social_media', 'blog', 'forum', 'government', 'corporate', 'academic', 'other')),
    region VARCHAR(10) DEFAULT 'KR',
    trust_score DECIMAL(3,2) DEFAULT 0.5 CHECK (trust_score >= 0.0 AND trust_score <= 1.0),
    crawl_policy JSONB DEFAULT '{}',
    robots_txt TEXT,
    robots_checked_at TIMESTAMP WITH TIME ZONE,
    last_crawl_at TIMESTAMP WITH TIME ZONE,
    last_success_at TIMESTAMP WITH TIME ZONE,
    failure_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('active', 'inactive', 'blocked', 'pending')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Task Queues
CREATE TABLE IF NOT EXISTS osint.task_queues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    queue_type VARCHAR(50) DEFAULT 'priority',
    max_workers INTEGER DEFAULT 5,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'paused')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tasks (Merged definition)
CREATE TABLE IF NOT EXISTS osint.tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID REFERENCES osint.collection_plans(id),
    task_type VARCHAR(100) NOT NULL, -- keyword_expansion, source_discovery, content_collection, etc.
    keywords TEXT[] DEFAULT '{}',
    sources TEXT[] DEFAULT '{}',
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'assigned', 'in_progress', 'completed', 'failed', 'cancelled')),
    assigned_to VARCHAR(255),
    payload JSONB DEFAULT '{}', -- Input parameters
    result JSONB DEFAULT '{}', -- Output data
    metadata JSONB DEFAULT '{}',
    dependencies TEXT[] DEFAULT '{}',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 3600,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Task Dependencies
CREATE TABLE IF NOT EXISTS osint.task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES osint.tasks(id) ON DELETE CASCADE,
    depends_on_task_id UUID NOT NULL REFERENCES osint.tasks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) DEFAULT 'completion',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(task_id, depends_on_task_id)
);

-- Worker Nodes
CREATE TABLE IF NOT EXISTS osint.worker_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id VARCHAR(255) NOT NULL UNIQUE,
    node_type VARCHAR(100) NOT NULL,
    capabilities TEXT[] DEFAULT '{}',
    max_concurrent_tasks INTEGER DEFAULT 5,
    current_load INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance')),
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES
-- =====================================================

-- Pension Schema Indexes
CREATE INDEX idx_collected_data_source ON pension.collected_data(source_id);
CREATE INDEX idx_collected_data_published ON pension.collected_data(published_at DESC);
CREATE INDEX idx_sentiment_data ON pension.sentiment_analysis(data_id);
CREATE INDEX idx_sentiment_analyzed ON pension.sentiment_analysis(analyzed_at DESC);
CREATE INDEX idx_persona_user ON pension.user_personas(user_identifier);
CREATE INDEX idx_alert_rule ON pension.alert_logs(rule_id);
CREATE INDEX idx_content_search ON pension.collected_data USING GIN(to_tsvector('korean', content));
CREATE INDEX idx_title_search ON pension.collected_data USING GIN(to_tsvector('korean', title));

-- OSINT Schema Indexes
CREATE INDEX idx_osint_keywords_type ON osint.keywords(keyword_type);
CREATE INDEX idx_osint_keywords_status ON osint.keywords(status);
CREATE INDEX idx_osint_keywords_text ON osint.keywords USING gin(to_tsvector('korean', keyword));
CREATE INDEX idx_osint_sources_host ON osint.sources(host);
CREATE INDEX idx_osint_sources_status ON osint.sources(status);
CREATE INDEX idx_osint_tasks_type ON osint.tasks(task_type);
CREATE INDEX idx_osint_tasks_status ON osint.tasks(status);
CREATE INDEX idx_osint_tasks_plan ON osint.tasks(plan_id);
CREATE INDEX idx_osint_tasks_created_at ON osint.tasks(created_at);

-- =====================================================
-- TRIGGERS (Updated At)
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_pension_data_sources_modtime BEFORE UPDATE ON pension.data_sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pension_user_personas_modtime BEFORE UPDATE ON pension.user_personas FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_pension_alert_rules_modtime BEFORE UPDATE ON pension.alert_rules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_osint_keywords_modtime BEFORE UPDATE ON osint.keywords FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_osint_sources_modtime BEFORE UPDATE ON osint.sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_osint_tasks_modtime BEFORE UPDATE ON osint.tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_osint_worker_nodes_modtime BEFORE UPDATE ON osint.worker_nodes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- SEED DATA
-- =====================================================

-- Pension Data Sources
INSERT INTO pension.data_sources (name, type, url) VALUES
    ('국민연금공단', 'official', 'https://www.nps.or.kr'),
    ('보건복지부', 'official', 'https://www.mohw.go.kr'),
    ('네이버 뉴스', 'news', 'https://news.naver.com'),
    ('다음 뉴스', 'news', 'https://news.daum.net'),
    ('클리앙', 'community', 'https://www.clien.net'),
    ('뽐뿌', 'community', 'https://www.ppomppu.co.kr'),
    ('구글 뉴스 RSS', 'rss', 'https://news.google.com/rss')
ON CONFLICT DO NOTHING;

-- Pension Alert Rules
INSERT INTO pension.alert_rules (name, condition, threshold_value, target_metric, notification_channels) VALUES
    ('부정 감성 급증', 'threshold', 0.7, 'negative_sentiment_ratio', '["email", "slack"]'),
    ('데이터 수집 중단', 'anomaly', 0, 'collection_rate', '["email"]'),
    ('키워드 급상승', 'pattern', 2.0, 'keyword_frequency_change', '["slack"]')
ON CONFLICT DO NOTHING;

-- OSINT Task Queues
INSERT INTO osint.task_queues (name, queue_type, max_workers, status) VALUES
    ('default', 'priority', 10, 'active'),
    ('high_priority', 'priority', 5, 'active'),
    ('background', 'fifo', 3, 'active')
ON CONFLICT DO NOTHING;

-- OSINT Seed Keywords
INSERT INTO osint.keywords (keyword, keyword_type, language, domain, status) VALUES
    ('연금', 'seed', 'ko', 'pension', 'approved'),
    ('투자', 'seed', 'ko', 'investment', 'approved'),
    ('은퇴', 'seed', 'ko', 'retirement', 'approved'),
    ('pension', 'seed', 'en', 'pension', 'approved'),
    ('retirement', 'seed', 'en', 'retirement', 'approved')
ON CONFLICT DO NOTHING;

-- OSINT Sources
INSERT INTO osint.sources (url, host, category, region, trust_score, status) VALUES
    ('https://news.naver.com', 'news.naver.com', 'news', 'KR', 0.9, 'active'),
    ('https://www.yonhapnews.co.kr', 'www.yonhapnews.co.kr', 'news', 'KR', 0.95, 'active'),
    ('https://www.mk.co.kr', 'www.mk.co.kr', 'news', 'KR', 0.8, 'active'),
    ('https://www.pension.co.kr', 'www.pension.co.kr', 'government', 'KR', 0.98, 'active'),
    ('https://www.nps.or.kr', 'www.nps.or.kr', 'government', 'KR', 1.0, 'active')
ON CONFLICT DO NOTHING;