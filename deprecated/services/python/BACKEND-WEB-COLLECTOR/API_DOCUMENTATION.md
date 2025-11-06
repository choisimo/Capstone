# Hybrid AI Collector Service API Documentation v2.0

## Overview

The Hybrid AI Collector Service v2.0 enhances the original web collector with AI-powered analysis capabilities, combining:

- **Gemini AI Integration**: Advanced pension sentiment analysis and content classification
- **ScrapeGraphAI Adapter**: Intelligent web scraping with multiple strategies
- **Original ChangeDetection.io**: Reliable web monitoring and change detection
- **Strategy Selection Engine**: Intelligent collection strategy recommendation

## Base URL

```
http://localhost:8000
```

## Authentication

The service inherits authentication from the configured ChangeDetection.io instance. Set the following environment variables:

```bash
export CHANGEDETECTION_URL="http://your-changedetection-instance"
export CHANGEDETECTION_API_KEY="your-api-key"
export GEMINI_API_KEY="your-gemini-api-key"
```

## API Endpoints

### Health Check

#### `GET /api/v2/health`

Check service health and configuration status.

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "services": {
    "changedetection": true,
    "gemini_ai": true,
    "smart_scraping": true,
    "perplexity": false
  },
  "configuration": {
    "ai_enabled": true,
    "smart_scraping_enabled": true,
    "strategy_selection": "auto"
  }
}
```

### AI Content Analysis

#### `POST /api/v2/analyze`

Perform comprehensive AI-powered analysis of web content.

**Request Body:**
```json
{
  "url": "https://example.com/pension-news",
  "content": "optional pre-fetched content",
  "strategy": "smart_scraper",
  "pension_focus": true
}
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "sentiment": "negative",
    "confidence": 0.85,
    "relevance_score": 0.95,
    "key_topics": ["국민연금", "보험료 인상", "연금개혁"],
    "summary": "정부의 국민연금 보험료 인상 계획에 대한 분석",
    "entities": ["정부", "보건복지부", "국민연금공단"],
    "policy_impact": "high",
    "demographic_focus": "general"
  },
  "strategy_used": "smart_scraper",
  "execution_time": 2.34,
  "confidence": 0.85,
  "recommendations": [
    "High confidence analysis - suitable for automated processing",
    "High pension relevance - priority for monitoring",
    "High policy impact - alert stakeholders"
  ]
}
```

### Strategy Recommendation

#### `POST /api/v2/recommend-strategy`

Get optimal collection strategy recommendation for a URL.

**Request Body:**
```json
{
  "url": "https://example.com/content",
  "content_hints": ["news", "government"],
  "historical_data": {}
}
```

**Response:**
```json
{
  "recommended_strategy": "smart_scraping",
  "confidence": 0.9,
  "reasoning": "정부 정책 문서로 정확한 분석이 필요; 연금 관련성이 매우 높음; AI 기반 지능형 수집으로 최고 품질 분석",
  "alternative_strategies": [
    {
      "strategy": "ai_enhanced",
      "confidence": 0.72,
      "pros": "Alternative approach using ai_enhanced",
      "cons": "Lower confidence than smart_scraping"
    }
  ]
}
```

### Search Query Generation

#### `POST /api/v2/generate-queries`

Generate optimized search queries for pension-related topics.

**Query Parameters:**
- `topic` (required): Topic for query generation
- `count` (optional, default=5): Number of queries to generate (1-20)

**Example Request:**
```
POST /api/v2/generate-queries?topic=연금개혁&count=5
```

**Response:**
```json
{
  "topic": "연금개혁",
  "queries": [
    "연금개혁 최신 동향 2024",
    "pension reform Korea latest",
    "국민연금 정책 변화 소식",
    "기초연금 인상 계획",
    "개인연금 세제혜택 개편"
  ],
  "count": 5,
  "generated_at": 1695648000
}
```

### Enhanced Watch Creation

#### `POST /api/v2/create-watch`

Create enhanced monitoring watch with AI-powered strategy selection.

**Request Body:**
```json
{
  "url": "https://example.com/pension-policy",
  "title": "Pension Policy Monitor",
  "instruction": "Monitor changes in pension policy announcements",
  "strategy": "ai_enhanced",
  "use_ai": true,
  "content_type": "government_policy",
  "pension_focus": true,
  "tags": ["pension", "policy"],
  "notification_urls": ["https://webhook.example.com/notify"],
  "recheck": true
}
```

**Response:**
```json
{
  "result": {
    "watch_id": "abc123",
    "status": "created",
    "url": "https://example.com/pension-policy"
  },
  "strategy_used": "ai_enhanced",
  "ai_enabled": true,
  "pension_focus": true
}
```

## Collection Strategies

### Traditional (`traditional`)
- Uses original ChangeDetection.io functionality only
- Reliable for basic change monitoring
- No AI analysis

### AI Enhanced (`ai_enhanced`)
- Combines ChangeDetection.io with Gemini AI analysis
- Suitable for government policies and academic papers
- Balanced approach with enhanced analysis

### Smart Scraping (`smart_scraping`)
- Uses ScrapeGraphAI for intelligent content extraction
- Best for high-value, complex content
- Maximum AI analysis capabilities

### Hybrid (`hybrid`)
- Intelligent strategy selection based on content analysis
- Automatically chooses optimal approach
- Recommended for varied content types

## Content Types

The service automatically classifies content into the following types:

- `news_article`: News and media content
- `government_policy`: Official government documents and policies
- `forum_discussion`: Community forums and discussion boards
- `academic_paper`: Research papers and academic content
- `social_media`: Social media posts and blogs
- `unknown`: Unclassified content

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2024-09-24T10:30:00Z"
}
```

## Rate Limits

- Gemini API: Follows Google's Gemini API rate limits
- Content analysis: 60 requests per minute
- Query generation: 30 requests per minute

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `GEMINI_MODEL` | Gemini model to use | `gemini-1.5-flash-8b` |
| `ENABLE_AI` | Enable AI features | `1` |
| `ENABLE_SMART_SCRAPING` | Enable ScrapeGraphAI | `1` |
| `STRATEGY_SELECTION` | Strategy selection mode | `auto` |
| `AI_CONFIDENCE_THRESHOLD` | Minimum confidence for AI decisions | `0.7` |
| `FALLBACK_STRATEGY` | Fallback when AI fails | `traditional` |

## Integration Examples

### Python Client

```python
import requests

# Analyze content
response = requests.post('http://localhost:8000/api/v2/analyze', json={
    'url': 'https://example.com/pension-news',
    'pension_focus': True
})
analysis = response.json()

# Create enhanced watch
watch_response = requests.post('http://localhost:8000/api/v2/create-watch', json={
    'url': 'https://gov.kr/pension-policy',
    'use_ai': True,
    'pension_focus': True
})
```

### JavaScript/Node.js

```javascript
const axios = require('axios');

// Get strategy recommendation
const strategyResponse = await axios.post('http://localhost:8000/api/v2/recommend-strategy', {
  url: 'https://example.com/content'
});

console.log('Recommended strategy:', strategyResponse.data.recommended_strategy);
```

## Monitoring and Logging

The service logs all operations and provides detailed metrics:

- Request/response times
- AI analysis confidence scores
- Strategy selection reasoning
- Error rates and types

## Performance Considerations

- Smart scraping operations may take 5-10 seconds
- Content analysis typically completes in 2-5 seconds
- Use appropriate timeouts for client requests
- Consider caching frequently analyzed URLs

## Support

For issues and feature requests, see:
- GitHub: [Repository URL]
- Documentation: `/docs` endpoint for interactive API docs
- Health endpoint: `/api/v2/health` for service status