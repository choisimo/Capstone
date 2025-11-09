package com.capstone.analysis.dto;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

public class SentimentDtos {
    
    public record SentimentAnalysisRequest(
            String text,
            String content_id
    ) {}
    
    public record SentimentAnalysisResponse(
            String content_id,
            double sentiment_score,
            String sentiment_label,
            double confidence,
            String model_version,
            Long analysis_id
    ) {}
    
    public record BatchSentimentRequest(
            List<SentimentAnalysisRequest> texts
    ) {}
    
    public record BatchSentimentResponse(
            List<SentimentAnalysisResponse> results,
            int total_processed,
            int success_count,
            int error_count
    ) {}
    
    public record SentimentHistory(
            Long id,
            String content_id,
            double sentiment_score,
            String sentiment_label,
            double confidence,
            OffsetDateTime analyzed_at
    ) {}
    
    public record SentimentStats(
            int total_analyses,
            int positive_count,
            int negative_count,
            int neutral_count,
            double avg_sentiment_score,
            double avg_confidence,
            OffsetDateTime start_date,
            OffsetDateTime end_date
    ) {}
}
