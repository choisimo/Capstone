package com.capstone.analysis.service;

import com.capstone.analysis.dto.AnalysisDtos.AnalysisType;
import com.capstone.analysis.dto.SentimentDtos.*;
import com.capstone.analysis.entity.SentimentAnalysisEntity;
import com.capstone.analysis.infrastructure.ColabClient;
import com.capstone.analysis.repository.SentimentAnalysisRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 감성 분석 서비스
 *
 * 텍스트의 감성을 분석하고 결과를 저장하는 비즈니스 로직을 담당합니다.
 * Colab ML 모델을 호출하며, 실패 시 Rule-based 로직으로 Fallback 처리합니다.
 */
@Service
@Slf4j
public class SentimentService {
    
    private final SentimentAnalysisRepository sentimentAnalysisRepository;
    private final ColabClient colabClient;
    private final ObjectMapper objectMapper;
    
    public SentimentService(SentimentAnalysisRepository sentimentAnalysisRepository,
                           ColabClient colabClient,
                           ObjectMapper objectMapper) {
        this.sentimentAnalysisRepository = sentimentAnalysisRepository;
        this.colabClient = colabClient;
        this.objectMapper = objectMapper;
    }
    
    /**
     * 단일 텍스트 감성 분석
     *
     * @param text 분석할 텍스트
     * @param contentId 컨텐츠 ID
     * @return SentimentAnalysisResponse 분석 결과
     */
    public SentimentAnalysisResponse analyzeSentiment(String text, String contentId) {
        try {
            // 1. Try Colab ML Model
            SentimentAnalysisRequest request = new SentimentAnalysisRequest(text, contentId);
            SentimentAnalysisResponse response = colabClient.analyzeSentiment(request);
            
            // Save result to DB
            saveAnalysisResult(
                    text,
                    contentId,
                    response.sentiment_score(),
                    response.sentiment_label(),
                    response.confidence(),
                    response.model_version(),
                    AnalysisType.SENTIMENT,
                    "GLOBAL",
                    null,
                    "colab:sentiment",
                    "sentiment",
                    null,
                    null
            );
            
            return response;
            
        } catch (Exception e) {
            log.warn("Colab analysis failed, falling back to rule-based logic: {}", e.getMessage());
            return analyzeSentimentFallback(text, contentId);
        }
    }

    private SentimentAnalysisResponse analyzeSentimentFallback(String text, String contentId) {
        double sentimentScore = 0.0; // -1 to 1
        String sentimentLabel = "neutral"; // positive, negative, neutral
        double confidence = 0.5; // Lower confidence for fallback
        String modelVersion = "fallback-rule-based-v1";
        
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
        
        SentimentAnalysisEntity saved = saveAnalysisResult(
                text,
                contentId,
                sentimentScore,
                sentimentLabel,
                confidence,
                modelVersion,
                AnalysisType.SENTIMENT,
                "GLOBAL",
                null,
                "fallback:rule-based",
                "sentiment",
                null,
                null
        );
        
        return new SentimentAnalysisResponse(
                contentId,
                sentimentScore,
                sentimentLabel,
                confidence,
                modelVersion,
                saved.getId()
        );
    }

    private SentimentAnalysisEntity saveAnalysisResult(
            String text,
            String contentId,
            double score,
            String label,
            double confidence,
            String version,
            AnalysisType analysisType,
            String aspect,
            String trueLabel,
            String source,
            String modelType,
            String trainingJobId,
            List<String> tags
    ) {
        SentimentAnalysisEntity entity = new SentimentAnalysisEntity();
        entity.setContentId(contentId);
        entity.setText(text);
        entity.setSentimentScore(score);
        entity.setSentimentLabel(label);
        entity.setConfidence(confidence);
        entity.setModelVersion(version);
        entity.setAnalyzedAt(OffsetDateTime.now());
        entity.setAnalysisType(analysisType.name());
        entity.setAspect(aspect);
        entity.setTrueLabel(trueLabel);
        entity.setSource(source);
        entity.setModelType(modelType);
        entity.setTrainingJobId(trainingJobId);
        entity.setTagsJson(writeTagsJson(tags));
        
        return sentimentAnalysisRepository.save(entity);
    }

    private String writeTagsJson(List<String> tags) {
        if (tags == null || tags.isEmpty()) {
            return null;
        }
        try {
            return objectMapper.writeValueAsString(tags);
        } catch (JsonProcessingException e) {
            log.warn("Failed to serialize tags to JSON: {}", e.getMessage());
            return null;
        }
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
