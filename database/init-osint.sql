-- OSINT Database Initialization Script
-- This script creates the necessary tables for the OSINT MSA services

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- OSINT PLANNING SERVICE TABLES
-- =====================================================

-- Keywords table for OSINT planning
CREATE TABLE osint_keywords (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword VARCHAR(255) NOT NULL,
    keyword_type VARCHAR(50) NOT NULL CHECK (keyword_type IN ('seed', 'expanded', 'alias')),
    expansion_method VARCHAR(100),
    parent_keyword_id UUID,
    confidence_score DECIMAL(3,2) DEFAULT 0.5,
    language VARCHAR(10) DEFAULT 'ko',
    domain VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'archived')),
    usage_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_keyword_id) REFERENCES osint_keywords(id) ON DELETE SET NULL
);

-- Keyword co-occurrences for expansion analysis
CREATE TABLE osint_keyword_cooccurrences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword1_id UUID NOT NULL,
    keyword2_id UUID NOT NULL,
    frequency INTEGER DEFAULT 1,
    context VARCHAR(500),
    confidence_score DECIMAL(3,2) DEFAULT 0.5,
    source VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (keyword1_id) REFERENCES osint_keywords(id) ON DELETE CASCADE,
    FOREIGN KEY (keyword2_id) REFERENCES osint_keywords(id) ON DELETE CASCADE,
    UNIQUE(keyword1_id, keyword2_id)
);

-- Keyword performance metrics
CREATE TABLE osint_keyword_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyword_id UUID NOT NULL,
    date DATE NOT NULL,
    search_volume INTEGER DEFAULT 0,
    result_count INTEGER DEFAULT 0,
    relevance_score DECIMAL(3,2) DEFAULT 0.0,
    sentiment_score DECIMAL(3,2) DEFAULT 0.0,
    source_diversity INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (keyword_id) REFERENCES osint_keywords(id) ON DELETE CASCADE,
    UNIQUE(keyword_id, date)
);

-- =====================================================
-- OSINT SOURCE REGISTRY TABLES
-- =====================================================

-- OSINT sources for collection
CREATE TABLE osint_sources (
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

-- Source tags for categorization
CREATE TABLE osint_source_tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL,
    tag VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES osint_sources(id) ON DELETE CASCADE,
    UNIQUE(source_id, tag)
);

-- Source performance metrics
CREATE TABLE osint_source_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL,
    date DATE NOT NULL,
    success_rate DECIMAL(5,4) DEFAULT 0.0 CHECK (success_rate >= 0.0 AND success_rate <= 1.0),
    avg_response_time DECIMAL(8,3) DEFAULT 0.0,
    documents_collected INTEGER DEFAULT 0,
    quality_score DECIMAL(3,2) DEFAULT 0.0 CHECK (quality_score >= 0.0 AND quality_score <= 1.0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES osint_sources(id) ON DELETE CASCADE,
    UNIQUE(source_id, date)
);

-- =====================================================
-- OSINT TASK ORCHESTRATOR TABLES
-- =====================================================

-- Task queues for orchestration
CREATE TABLE osint_task_queues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    queue_type VARCHAR(50) DEFAULT 'priority',
    max_workers INTEGER DEFAULT 5,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'paused')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- OSINT tasks
CREATE TABLE osint_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_type VARCHAR(100) NOT NULL CHECK (task_type IN ('keyword_expansion', 'source_discovery', 'content_collection', 'sentiment_analysis', 'alert_generation')),
    keywords TEXT[] DEFAULT '{}',
    sources TEXT[] DEFAULT '{}',
    priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'assigned', 'in_progress', 'completed', 'failed', 'cancelled')),
    assigned_to VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    dependencies TEXT[] DEFAULT '{}',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 3600,
    expected_results INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Task results
CREATE TABLE osint_task_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    result_type VARCHAR(100) NOT NULL,
    data JSONB DEFAULT '{}',
    quality_score DECIMAL(3,2) DEFAULT 0.0 CHECK (quality_score >= 0.0 AND quality_score <= 1.0),
    confidence_score DECIMAL(3,2) DEFAULT 0.0 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES osint_tasks(id) ON DELETE CASCADE
);

-- Task dependencies
CREATE TABLE osint_task_dependencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL,
    depends_on_task_id UUID NOT NULL,
    dependency_type VARCHAR(50) DEFAULT 'completion',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES osint_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (depends_on_task_id) REFERENCES osint_tasks(id) ON DELETE CASCADE,
    UNIQUE(task_id, depends_on_task_id)
);

-- Worker nodes for task execution
CREATE TABLE osint_worker_nodes (
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
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Keywords indexes
CREATE INDEX idx_osint_keywords_type ON osint_keywords(keyword_type);
CREATE INDEX idx_osint_keywords_status ON osint_keywords(status);
CREATE INDEX idx_osint_keywords_domain ON osint_keywords(domain);
CREATE INDEX idx_osint_keywords_created_at ON osint_keywords(created_at);
CREATE INDEX idx_osint_keywords_keyword_text ON osint_keywords USING gin(to_tsvector('korean', keyword));

-- Sources indexes
CREATE INDEX idx_osint_sources_host ON osint_sources(host);
CREATE INDEX idx_osint_sources_category ON osint_sources(category);
CREATE INDEX idx_osint_sources_status ON osint_sources(status);
CREATE INDEX idx_osint_sources_trust_score ON osint_sources(trust_score);
CREATE INDEX idx_osint_sources_last_crawl ON osint_sources(last_crawl_at);

-- Tasks indexes
CREATE INDEX idx_osint_tasks_type ON osint_tasks(task_type);
CREATE INDEX idx_osint_tasks_status ON osint_tasks(status);
CREATE INDEX idx_osint_tasks_priority ON osint_tasks(priority);
CREATE INDEX idx_osint_tasks_assigned_to ON osint_tasks(assigned_to);
CREATE INDEX idx_osint_tasks_created_at ON osint_tasks(created_at);
CREATE INDEX idx_osint_tasks_keywords ON osint_tasks USING gin(keywords);

-- Worker nodes indexes
CREATE INDEX idx_osint_workers_node_type ON osint_worker_nodes(node_type);
CREATE INDEX idx_osint_workers_status ON osint_worker_nodes(status);
CREATE INDEX idx_osint_workers_capabilities ON osint_worker_nodes USING gin(capabilities);
CREATE INDEX idx_osint_workers_heartbeat ON osint_worker_nodes(last_heartbeat);

-- =====================================================
-- TRIGGERS FOR UPDATED_AT
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to relevant tables
CREATE TRIGGER update_osint_keywords_updated_at BEFORE UPDATE ON osint_keywords FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_osint_sources_updated_at BEFORE UPDATE ON osint_sources FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_osint_task_queues_updated_at BEFORE UPDATE ON osint_task_queues FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_osint_tasks_updated_at BEFORE UPDATE ON osint_tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_osint_worker_nodes_updated_at BEFORE UPDATE ON osint_worker_nodes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- SAMPLE DATA INSERTION
-- =====================================================

-- Insert sample task queue
INSERT INTO osint_task_queues (name, queue_type, max_workers, status) VALUES
('default', 'priority', 10, 'active'),
('high_priority', 'priority', 5, 'active'),
('background', 'fifo', 3, 'active');

-- Insert sample keywords
INSERT INTO osint_keywords (keyword, keyword_type, language, domain, status) VALUES
('연금', 'seed', 'ko', 'pension', 'approved'),
('투자', 'seed', 'ko', 'investment', 'approved'),
('은퇴', 'seed', 'ko', 'retirement', 'approved'),
('pension', 'seed', 'en', 'pension', 'approved'),
('retirement', 'seed', 'en', 'retirement', 'approved'),
('annuity', 'seed', 'en', 'pension', 'approved');

-- Insert sample sources
INSERT INTO osint_sources (url, host, category, region, trust_score, status) VALUES
('https://news.naver.com', 'news.naver.com', 'news', 'KR', 0.9, 'active'),
('https://www.yonhapnews.co.kr', 'www.yonhapnews.co.kr', 'news', 'KR', 0.95, 'active'),
('https://www.mk.co.kr', 'www.mk.co.kr', 'news', 'KR', 0.8, 'active'),
('https://www.pension.co.kr', 'www.pension.co.kr', 'government', 'KR', 0.98, 'active'),
('https://www.nps.or.kr', 'www.nps.or.kr', 'government', 'KR', 1.0, 'active');

-- Insert sample tags
INSERT INTO osint_source_tags (source_id, tag) 
SELECT id, 'pension' FROM osint_sources WHERE host IN ('www.pension.co.kr', 'www.nps.or.kr');

INSERT INTO osint_source_tags (source_id, tag) 
SELECT id, 'news' FROM osint_sources WHERE category = 'news';

-- Insert sample worker node
INSERT INTO osint_worker_nodes (node_id, node_type, capabilities, max_concurrent_tasks, status) VALUES
('worker-001', 'collector', ARRAY['content_collection', 'source_discovery'], 5, 'active'),
('worker-002', 'analyzer', ARRAY['sentiment_analysis', 'keyword_expansion'], 3, 'active'),
('worker-003', 'alert', ARRAY['alert_generation'], 2, 'active');

COMMIT;