package com.capstone.analysis.dto;

import java.time.OffsetDateTime;
import java.util.List;

public class TrendDtos {
    
    public record TrendAnalysisRequest(
            String period,
            String entity,
            OffsetDateTime start_date,
            OffsetDateTime end_date
    ) {}
    
    public record TrendItem(
            OffsetDateTime date,
            double sentiment_score,
            int volume,
            List<String> keywords
    ) {}
    
    public record TrendAnalysisResponse(
            String period,
            String entity,
            String trend_direction,
            double trend_strength,
            List<TrendItem> data_points,
            String summary
    ) {}
    
    public record PopularTrend(
            String entity,
            int volume,
            double sentiment_score,
            String trend_direction,
            List<String> top_keywords
    ) {}
    
    public record TrendingKeyword(
            String keyword,
            int frequency,
            double importance_score,
            String sentiment
    ) {}
}
