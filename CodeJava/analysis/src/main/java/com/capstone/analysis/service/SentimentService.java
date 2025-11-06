package com.capstone.analysis.service;

import com.capstone.analysis.dto.SentimentDtos.*;
import com.capstone.analysis.entity.SentimentAnalysisEntity;
import com.capstone.analysis.repository.SentimentAnalysisRepository;
import org.springframework.stereotype.Service;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 감성 분석 서비스
 * 
 * 텍스트의 감성을 분석하고 결과를 저장하는 비즈니스 로직을 담당합니다.
 * 실제 ML 모델 호출은 추후 구현 예정입니다.
 */
@Service
public class SentimentService {
    
    private final SentimentAnalysisRepository sentimentAnalysisRepository;
    
    public SentimentService(SentimentAnalysisRepository sentimentAnalysisRepository) {
        this.sentimentAnalysisRepository = sentimentAnalysisRepository;
    }
    
    /**
     * 단일 텍스트 감성 분석
     * 
     * @param text 분석할 텍스트
     * @param contentId 컨텐츠 ID
     * @return SentimentAnalysisResponse 분석 결과
     */
    public SentimentAnalysisResponse analyzeSentiment(String text, String contentId) {
        // TODO: Implement actual ML model inference
        // For now, use simple rule-based logic
        
        double sentimentScore = 0.0; // -1 to 1
        String sentimentLabel = "neutral"; // positive, negative, neutral
        double confidence = 0.85;
        String modelVersion = "v1.0.0";
        
        // Simple placeholder logic based on text content
        if (text != null && !text.isEmpty()) {
            if (text.contains("좋") || text.contains("great") || text.contains("excellent")) {
                sentimentScore = 0.7;
                sentimentLabel = "positive";
            } else if (text.contains("나쁘") || text.contains("bad") || text.contains("terrible")) {
                sentimentScore = -0.7;
                sentimentLabel = "negative";
            }
        }
        
        // Save to database
        SentimentAnalysisEntity entity = new SentimentAnalysisEntity();
        entity.setContentId(contentId);
        entity.setText(text);
        entity.setSentimentScore(sentimentScore);
        entity.setSentimentLabel(sentimentLabel);
        entity.setConfidence(confidence);
        entity.setModelVersion(modelVersion);
        entity.setAnalyzedAt(OffsetDateTime.now());
        
        SentimentAnalysisEntity saved = sentimentAnalysisRepository.save(entity);
        
        return new SentimentAnalysisResponse(
                contentId,
                sentimentScore,
                sentimentLabel,
                confidence,
                modelVersion,
                saved.getId()
        );
    }
    
    /**
     * 배치 감성 분석
     * 
     * @param requests 분석 요청 목록
     * @return BatchSentimentResponse 배치 처리 결과
     */
    public BatchSentimentResponse batchAnalyzeSentiment(List<SentimentAnalysisRequest> requests) {
        // TODO: Implement batch processing with async/parallel execution
        
        List<SentimentAnalysisResponse> results = new ArrayList<>();
        int successCount = 0;
        int errorCount = 0;
        
        for (SentimentAnalysisRequest request : requests) {
            try {
                SentimentAnalysisResponse response = analyzeSentiment(
                        request.text(), 
                        request.content_id()
                );
                results.add(response);
                successCount++;
            } catch (Exception e) {
                errorCount++;
            }
        }
        
        return new BatchSentimentResponse(
                results,
                requests.size(),
                successCount,
                errorCount
        );
    }
    
    /**
     * 감성 분석 히스토리 조회
     * 
     * @param contentId 컨텐츠 ID
     * @param limit 조회 개수
     * @return List<SentimentHistory> 히스토리 목록
     */
    public List<SentimentHistory> getSentimentHistory(String contentId, int limit) {
        // Query database for sentiment history
        List<SentimentAnalysisEntity> entities = sentimentAnalysisRepository
                .findByContentIdOrderByAnalyzedAtDesc(contentId)
                .stream()
                .limit(limit)
                .collect(Collectors.toList());
        
        return entities.stream()
                .map(entity -> new SentimentHistory(
                        entity.getId(),
                        entity.getContentId(),
                        entity.getSentimentScore(),
                        entity.getSentimentLabel(),
                        entity.getConfidence(),
                        entity.getAnalyzedAt()
                ))
                .collect(Collectors.toList());
    }
    
    /**
     * 감성 분석 통계 조회
     * 
     * @param startDate 시작 날짜
     * @param endDate 종료 날짜
     * @return SentimentStats 통계 데이터
     */
    public SentimentStats getSentimentStatistics(String startDate, String endDate) {
        // Parse date range
        OffsetDateTime start = startDate != null 
                ? OffsetDateTime.parse(startDate + "T00:00:00Z") 
                : OffsetDateTime.now().minusDays(30);
        OffsetDateTime end = endDate != null 
                ? OffsetDateTime.parse(endDate + "T23:59:59Z") 
                : OffsetDateTime.now();
        
        // Get all analyses in date range
        List<SentimentAnalysisEntity> analyses = sentimentAnalysisRepository
                .findByAnalyzedAtBetween(start, end);
        
        // Calculate statistics
        int totalAnalyses = analyses.size();
        long positiveCount = sentimentAnalysisRepository
                .countBySentimentLabelAndDateRange("positive", start, end);
        long negativeCount = sentimentAnalysisRepository
                .countBySentimentLabelAndDateRange("negative", start, end);
        long neutralCount = sentimentAnalysisRepository
                .countBySentimentLabelAndDateRange("neutral", start, end);
        
        Double avgSentimentScore = sentimentAnalysisRepository
                .calculateAverageSentimentScore(start, end);
        Double avgConfidence = sentimentAnalysisRepository
                .calculateAverageConfidence(start, end);
        
        return new SentimentStats(
                totalAnalyses,
                (int) positiveCount,
                (int) negativeCount,
                (int) neutralCount,
                avgSentimentScore != null ? avgSentimentScore : 0.0,
                avgConfidence != null ? avgConfidence : 0.0,
                start,
                end
        );
    }
}
