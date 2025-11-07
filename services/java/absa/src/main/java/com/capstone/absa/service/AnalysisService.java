package com.capstone.absa.service;

import com.capstone.absa.dto.AnalysisDtos.*;
import com.capstone.absa.entity.ABSAAnalysisEntity;
import com.capstone.absa.repository.ABSAAnalysisRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.*;

/**
 * ABSA 분석 서비스
 * 
 * 속성 기반 감성 분석(ABSA)을 수행하는 비즈니스 로직을 처리합니다.
 * Reference: BACKEND-ABSA-SERVICE/app/routers/analysis.py
 */
@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class AnalysisService {

    private final ABSAAnalysisRepository analysisRepository;

    /**
     * ABSA 분석 수행
     * 
     * 텍스트와 속성 리스트를 받아 각 속성별 감성을 분석합니다.
     * 
     * @param request 분석 요청
     * @return 분석 결과
     */
    @Transactional
    public AnalyzeResponse analyzeABSA(AnalyzeRequest request) {
        log.info("Analyzing ABSA for text: {}", request.text().substring(0, Math.min(100, request.text().length())));
        
        String text = request.text();
        String contentId = request.contentId() != null ? request.contentId() : UUID.randomUUID().toString();
        
        // 속성 리스트 (제공되지 않으면 기본값 사용)
        List<String> aspects = request.aspects() != null && !request.aspects().isEmpty()
            ? request.aspects()
            : List.of("수익률", "안정성", "관리비용", "서비스");
        
        // 속성별 감성 분석 수행
        Map<String, AspectSentiment> aspectSentiments = new HashMap<>();
        for (String aspect : aspects) {
            double sentimentScore = analyzeAspectSentiment(text, aspect);
            double confidence = 0.5 + 0.5 * Math.min(1.0, Math.abs(sentimentScore));
            
            aspectSentiments.put(aspect, new AspectSentiment(
                sentimentScore,
                getSentimentLabel(sentimentScore),
                Math.round(confidence * 1000.0) / 1000.0
            ));
        }
        
        // 전체 감성 점수 계산
        double overallSentiment = aspectSentiments.values().stream()
            .mapToDouble(AspectSentiment::sentimentScore)
            .average()
            .orElse(0.0);
        
        // 전체 신뢰도 계산
        double meanAbs = aspectSentiments.values().stream()
            .mapToDouble(as -> Math.abs(as.sentimentScore()))
            .average()
            .orElse(0.0);
        double overallConfidence = Math.round((0.5 + 0.5 * Math.min(1.0, meanAbs)) * 1000.0) / 1000.0;
        
        // 분석 결과 저장
        Map<String, Map<String, Object>> aspectSentimentsMap = new HashMap<>();
        aspectSentiments.forEach((key, value) -> {
            Map<String, Object> sentimentMap = new HashMap<>();
            sentimentMap.put("sentiment_score", value.sentimentScore());
            sentimentMap.put("sentiment_label", value.sentimentLabel());
            sentimentMap.put("confidence", value.confidence());
            aspectSentimentsMap.put(key, sentimentMap);
        });
        
        ABSAAnalysisEntity analysis = ABSAAnalysisEntity.builder()
            .id(UUID.randomUUID().toString())
            .contentId(contentId)
            .text(text.substring(0, Math.min(1000, text.length())))
            .aspects(aspects)
            .aspectSentiments(aspectSentimentsMap)
            .overallSentiment(overallSentiment)
            .confidenceScore(overallConfidence)
            .build();
        
        ABSAAnalysisEntity saved = analysisRepository.save(analysis);
        
        log.info("ABSA analysis completed with ID: {}", saved.getId());
        
        return new AnalyzeResponse(
            saved.getId(),
            contentId,
            text.substring(0, Math.min(200, text.length())),
            aspects,
            aspectSentiments,
            new OverallSentiment(overallSentiment, getSentimentLabel(overallSentiment)),
            overallConfidence,
            OffsetDateTime.now().toString()
        );
    }

    /**
     * 특정 컨텐츠의 분석 히스토리 조회
     * 
     * @param contentId 컨텐츠 ID
     * @param limit 조회할 최대 개수
     * @return 분석 히스토리
     */
    public HistoryResponse getAnalysisHistory(String contentId, int limit) {
        log.info("Getting analysis history for content ID: {}", contentId);
        
        PageRequest pageRequest = PageRequest.of(0, limit);
        Page<ABSAAnalysisEntity> analysesPage = analysisRepository
            .findByContentIdOrderByCreatedAtDesc(contentId, pageRequest);
        
        List<HistoryItem> items = analysesPage.getContent().stream()
            .map(analysis -> {
                Map<String, AspectSentiment> aspectSentiments = new HashMap<>();
                if (analysis.getAspectSentiments() != null) {
                    analysis.getAspectSentiments().forEach((key, value) -> {
                        aspectSentiments.put(key, new AspectSentiment(
                            ((Number) value.get("sentiment_score")).doubleValue(),
                            (String) value.get("sentiment_label"),
                            ((Number) value.get("confidence")).doubleValue()
                        ));
                    });
                }
                
                return new HistoryItem(
                    analysis.getId(),
                    analysis.getAspects() != null ? analysis.getAspects() : List.of(),
                    aspectSentiments,
                    analysis.getOverallSentiment() != null ? analysis.getOverallSentiment() : 0.0,
                    analysis.getConfidenceScore() != null ? analysis.getConfidenceScore() : 0.0,
                    analysis.getCreatedAt() != null ? analysis.getCreatedAt().toString() : null
                );
            })
            .toList();
        
        log.info("Found {} analysis records for content ID: {}", items.size(), contentId);
        
        return new HistoryResponse(
            contentId,
            items,
            items.size(),
            limit,
            new PaginationMeta(items.size(), limit, 0)
        );
    }

    /**
     * 배치 ABSA 분석
     * 
     * 여러 텍스트를 한 번에 분석합니다.
     * 
     * @param requests 분석 요청 리스트
     * @return 배치 분석 결과
     */
    @Transactional
    public BatchAnalyzeResponse batchAnalyze(List<AnalyzeRequest> requests) {
        log.info("Batch analyzing {} texts", requests.size());
        
        List<Object> results = new ArrayList<>();
        int successCount = 0;
        int errorCount = 0;
        
        for (AnalyzeRequest request : requests) {
            try {
                AnalyzeResponse result = analyzeABSA(request);
                results.add(result);
                successCount++;
            } catch (Exception e) {
                log.error("Error analyzing text: {}", e.getMessage());
                results.add(new BatchErrorItem(
                    e.getMessage(),
                    request.text().substring(0, Math.min(100, request.text().length()))
                ));
                errorCount++;
            }
        }
        
        log.info("Batch analysis completed: {} success, {} errors", successCount, errorCount);
        
        return new BatchAnalyzeResponse(
            results,
            requests.size(),
            successCount,
            errorCount
        );
    }

    /**
     * 속성별 감성 점수 계산 (간단한 규칙 기반)
     * 
     * 실제 환경에서는 트랜스포머 기반 모델을 사용합니다.
     * TODO: Implement actual ML model inference
     * 
     * @param text 분석할 텍스트
     * @param aspect 속성
     * @return 감성 점수 (-1.0 ~ 1.0)
     */
    private double analyzeAspectSentiment(String text, String aspect) {
        String textLower = text.toLowerCase();
        String aspectLower = aspect.toLowerCase();
        
        // 긍정/부정 키워드 (속성별로 다르게 적용 가능)
        List<String> positiveKeywords = List.of("좋다", "훌륭", "만족", "우수", "높은", "안정", "저렴");
        List<String> negativeKeywords = List.of("나쁘다", "불만", "부족", "높다", "비싸다", "불안");
        
        double score = 0.0;
        
        // 속성 언급 확인
        if (textLower.contains(aspectLower)) {
            // 속성 주변 텍스트에서 감성 분석
            for (String keyword : positiveKeywords) {
                if (textLower.contains(keyword)) {
                    score += 0.3;
                }
            }
            
            for (String keyword : negativeKeywords) {
                if (textLower.contains(keyword)) {
                    score -= 0.3;
                }
            }
        }
        
        // 점수 정규화 (-1 ~ 1)
        return Math.max(-1.0, Math.min(1.0, score));
    }

    /**
     * 감성 점수를 레이블로 변환
     * 
     * @param score 감성 점수
     * @return 감성 레이블 (positive, negative, neutral)
     */
    private String getSentimentLabel(double score) {
        if (score > 0.3) {
            return "positive";
        } else if (score < -0.3) {
            return "negative";
        } else {
            return "neutral";
        }
    }
}
