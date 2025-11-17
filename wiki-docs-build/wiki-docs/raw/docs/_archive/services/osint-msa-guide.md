# OSINT MSA Implementation Guide

## Overview

This document describes the implementation of the OSINT (Open Source Intelligence) Microservices Architecture for pre-collection intelligence gathering, designed to enhance the pension sentiment analysis system with intelligent keyword expansion and source discovery.

## Architecture

The OSINT MSA consists of three core services:

### 1. OSINT Planning Service (Port 8003)
**Purpose**: Intelligent keyword expansion and research planning
- **Endpoint**: `http://localhost:8003`
- **Database Tables**: `osint_keywords`, `osint_keyword_cooccurrences`, `osint_keyword_metrics`
- **Key Features**:
  - Korean morpheme analysis for keyword expansion
  - Synonym and co-occurrence expansion methods
  - Keyword approval workflow
  - Performance tracking and analytics

### 2. OSINT Source Registry Service (Port 8004)
**Purpose**: Dynamic source discovery and validation
- **Endpoint**: `http://localhost:8004`
- **Database Tables**: `osint_sources`, `osint_source_tags`, `osint_source_metrics`
- **Key Features**:
  - Source validation with robots.txt checking
  - Trust scoring based on domain authority
  - Bulk source registration
  - Crawlable source filtering

### 3. OSINT Task Orchestrator Service (Port 8005)
**Purpose**: Priority-based task queue management and worker coordination
- **Endpoint**: `http://localhost:8005`
- **Database Tables**: `osint_tasks`, `osint_task_results`, `osint_task_dependencies`, `osint_worker_nodes`, `osint_task_queues`
- **Key Features**:
  - Weighted priority scoring for task orchestration
  - Task dependency management
  - Worker node registration and heartbeat monitoring
  - Event-driven task lifecycle management

## Infrastructure Components

### Database
- **PostgreSQL** (Port 5433): Persistent storage for all OSINT data
- **Redis** (Port 6380): Caching and session storage
- **Kafka** (Port 9093): Event streaming for service communication

### Event-Driven Communication
Services communicate through Kafka events:
- `task.created`: New task added to queue
- `task.updated`: Task status changes
- `task.result`: Task completion with results
- `worker.registered`: New worker node available
- `keyword.expanded`: New keywords discovered
- `source.validated`: Source validation completed

## Quick Start

### 1. Start OSINT Services
```bash
# Start all OSINT services and infrastructure
make osint-up

# Check service health
make osint-health

# View service status
make osint-status
```

### 2. Initialize Database
```bash
# Initialize OSINT database with schemas and sample data
make osint-db-init
```

### 3. Run Integration Tests
```bash
# Test all service endpoints
make osint-test
```

## API Examples

### Planning Service - Keyword Management

#### Create Keyword
```bash
curl -X POST http://localhost:8003/api/v1/keywords \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "연금개혁",
    "keyword_type": "seed",
    "domain": "pension",
    "language": "ko"
  }'
```

#### Expand Keywords
```bash
curl -X POST http://localhost:8003/api/v1/keywords/expand \
  -H "Content-Type: application/json" \
  -d '{
    "base_keywords": ["연금", "투자"],
    "expansion_methods": ["morpheme", "synonym", "cooccurrence"],
    "max_results": 50
  }'
```

### Source Registry - Source Management

#### Register Source
```bash
curl -X POST http://localhost:8004/api/v1/sources \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://pension-news.example.com",
    "category": "news",
    "region": "KR",
    "tags": ["pension", "government"]
  }'
```

#### Get Crawlable Sources
```bash
curl "http://localhost:8004/api/v1/sources/crawlable?trust_score_min=0.7&limit=100"
```

### Task Orchestrator - Task Management

#### Create Collection Task
```bash
curl -X POST http://localhost:8005/api/v1/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "content_collection",
    "keywords": ["연금", "투자", "은퇴"],
    "sources": ["https://news.naver.com", "https://www.yonhapnews.co.kr"],
    "priority": "high",
    "expected_results": 100
  }'
```

#### Register Worker
```bash
curl -X POST http://localhost:8005/api/v1/tasks/workers \
  -H "Content-Type: application/json" \
  -d '{
    "node_id": "collector-worker-001",
    "node_type": "content_collector",
    "capabilities": ["content_collection", "source_discovery"],
    "max_concurrent_tasks": 5
  }'
```

#### Get Task Assignment
```bash
curl -X POST http://localhost:8005/api/v1/tasks/assign \
  -H "Content-Type: application/json" \
  -d '{
    "worker_capabilities": ["content_collection"],
    "max_tasks": 3
  }'
```

## Service Integration Flow

### 1. Intelligence Gathering Workflow
```
1. Planning Service expands seed keywords → Enhanced keyword list
2. Source Registry validates/discovers sources → Trusted source list  
3. Task Orchestrator creates collection tasks → Prioritized task queue
4. Workers pull tasks and collect content → Raw content data
5. Analysis Service processes content → Sentiment scores
6. Alert Service generates notifications → User alerts
```

### 2. Event Flow Example
```
Planning Service: keyword.expanded → Task Orchestrator
Source Registry: source.validated → Task Orchestrator  
Task Orchestrator: task.created → Workers
Workers: task.completed → Analysis Service
Analysis Service: analysis.completed → Alert Service
```

## Monitoring and Management

### Service Health Monitoring
```bash
# Check all service health endpoints
make osint-health

# Monitor services continuously
make osint-monitor

# View service logs
make osint-logs

# View specific service logs
make osint-logs-planning
make osint-logs-source
make osint-logs-orchestrator
```

### Database Management
```bash
# Backup database
make osint-backup

# Restore database
make osint-restore BACKUP_FILE=backups/osint-db-20231201-120000.sql

# Connect to database
docker-compose -f docker-compose.osint.yml exec osint-postgres psql -U osint_user -d osint_db
```

### Service Scaling
```bash
# Scale orchestrator service
make osint-scale-orchestrator REPLICAS=3

# Restart specific service
make osint-restart-planning
```

## Configuration

### Environment Variables

#### Common Settings
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka broker addresses
- `ENVIRONMENT`: deployment environment (development/production)
- `LOG_LEVEL`: logging level (DEBUG/INFO/WARN/ERROR)

#### Planning Service Specific
- `MAX_EXPANSION_RESULTS`: Maximum keywords per expansion (default: 100)
- `MORPHEME_ANALYZER`: Korean morpheme analyzer type (default: "mecab")
- `EXPANSION_CONFIDENCE_THRESHOLD`: Minimum confidence for expansion (default: 0.3)

#### Source Registry Specific
- `ROBOTS_TXT_CACHE_TTL`: Robots.txt cache duration (default: 86400s)
- `SOURCE_VALIDATION_TIMEOUT`: Source validation timeout (default: 30s)
- `TRUST_SCORE_THRESHOLD`: Minimum trust score for sources (default: 0.3)

#### Task Orchestrator Specific
- `MAX_QUEUE_SIZE`: Maximum tasks in queue (default: 10000)
- `TASK_TIMEOUT_DEFAULT`: Default task timeout (default: 3600s)
- `WORKER_HEARTBEAT_TIMEOUT`: Worker heartbeat timeout (default: 300s)

## Database Schema

### Key Tables

#### osint_keywords
- Core keyword storage with expansion tracking
- Supports Korean/English keywords
- Confidence scoring and approval workflow

#### osint_sources
- Source registry with trust scoring
- Robots.txt compliance checking
- Performance metrics tracking

#### osint_tasks
- Task queue with priority management
- Dependency tracking between tasks
- Retry logic and error handling

#### osint_worker_nodes
- Worker registration and capability tracking
- Load balancing and heartbeat monitoring
- Dynamic scaling support

## Performance Considerations

### Indexing Strategy
- Text search indexes on keywords using PostgreSQL's Korean text search
- Composite indexes on frequently queried combinations
- Partial indexes on active/pending status fields

### Caching Strategy
- Redis caching for robots.txt responses (24h TTL)
- Source validation results cached (1h TTL)
- Keyword expansion results cached (30min TTL)

### Queue Management
- Priority-based task scheduling with weighted scoring
- Dead letter queue for failed tasks
- Rate limiting to prevent source overload

## Troubleshooting

### Common Issues

#### Services Not Starting
```bash
# Check container logs
make osint-logs

# Verify network connectivity
docker network ls | grep osint

# Check service dependencies
make osint-status
```

#### Database Connection Issues
```bash
# Test database connectivity
docker-compose -f docker-compose.osint.yml exec osint-postgres pg_isready -U osint_user

# Check database logs
make osint-logs-postgres
```

#### Event Publishing Issues
```bash
# Check Kafka connectivity
docker-compose -f docker-compose.osint.yml exec osint-kafka kafka-topics --bootstrap-server localhost:9092 --list

# Monitor Kafka logs
make osint-logs-kafka
```

### Performance Tuning

#### Database Optimization
- Monitor slow query log
- Analyze query execution plans
- Adjust connection pool sizes

#### Memory Usage
- Monitor Redis memory usage
- Tune JVM settings for Kafka
- Adjust worker concurrency limits

## Security Considerations

### Data Protection
- All inter-service communication uses internal Docker network
- Database credentials stored in environment variables
- Rate limiting to prevent abuse

### Source Validation
- Robots.txt compliance checking
- Trust scoring to filter unreliable sources
- Timeout controls to prevent hanging requests

## Integration with Existing Services

### Web Collector Integration
- OSINT services provide enhanced keyword lists to collector
- Dynamic source lists replace static configuration
- Priority-based collection scheduling

### Analysis Service Integration
- Enriched content metadata from OSINT planning
- Source trust scores for confidence weighting
- Event-driven processing triggers

### Alert Service Integration
- Keyword-specific alert thresholds
- Source-based alert routing
- Priority-aware notification delivery

## Development and Testing

### Local Development
```bash
# Start services in development mode
make osint-dev

# Run individual service tests
cd BACKEND-OSINT-PLANNING-SERVICE && python -m pytest
cd BACKEND-OSINT-SOURCE-SERVICE && python -m pytest  
cd BACKEND-OSINT-ORCHESTRATOR-SERVICE && python -m pytest
```

### API Testing
```bash
# Run integration tests
make osint-test

# Test individual endpoints
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
```

This OSINT MSA implementation provides a robust foundation for intelligent content collection with Korean language support, dynamic source discovery, and event-driven task orchestration.