package com.capstone.absa.service;

import com.capstone.absa.dto.AnalysisDto.*;
import com.capstone.absa.model.ABSAAnalysis;
import com.capstone.absa.repository.ABSAAnalysisRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class ABSAAnalysisService {

    private final ABSAAnalysisRepository analysisRepository;

    /**
     * 속성 기반 감성 분석 수행
     */
    @Transactional
    public AnalyzeResponse analyzeABSA(AnalyzeRequest request) {
        String text = request.getText();
        if (text == null || text.isEmpty()) {
            throw new IllegalArgumentException("Text is required");
        }

        // 속성 리스트 (제공되지 않으면 기본값 사용)
        List<String> aspects = Optional.ofNullable(request.getAspects())
                .orElse(Arrays.asList("수익률", "안정성", "관리비용", "서비스"));
        
        String contentId = Optional.ofNullable(request.getContentId())
                .orElse(UUID.randomUUID().toString());

        // 속성별 감성 분석
        Map<String, AspectSentiment> aspectSentiments = new HashMap<>();
        for (String aspect : aspects) {
            double sentimentScore = analyzeAspectSentiment(text, aspect);
            double aspectConfidence = 0.5 + 0.5 * Math.min(1.0, Math.abs(sentimentScore));
            
            aspectSentiments.put(aspect, AspectSentiment.builder()
                    .sentimentScore(sentimentScore)
                    .sentimentLabel(getSentimentLabel(sentimentScore))
                    .confidence(Math.round(aspectConfidence * 1000.0) / 1000.0)
                    .build());
        }

        // 전체 감성 점수 계산
        double overallSentiment = aspectSentiments.values().stream()
                .mapToDouble(AspectSentiment::getSentimentScore)
                .average()
                .orElse(0.0);

        // 전체 신뢰도 계산
        double meanAbs = aspectSentiments.values().stream()
                .mapToDouble(v -> Math.abs(v.getSentimentScore()))
                .average()
                .orElse(0.0);
        double overallConfidence = 0.5 + 0.5 * Math.min(1.0, meanAbs);

        // DB에 저장
        Map<String, ABSAAnalysis.AspectSentimentResult> dbAspectSentiments = aspectSentiments.entrySet().stream()
                .collect(Collectors.toMap(
                        Map.Entry::getKey,
                        e -> new ABSAAnalysis.AspectSentimentResult(
                                e.getValue().getSentimentScore(),
                                e.getValue().getSentimentLabel(),
                                e.getValue().getConfidence()
                        )
                ));

        ABSAAnalysis analysis = ABSAAnalysis.builder()
                .contentId(contentId)
                .text(text.length() > 1000 ? text.substring(0, 1000) : text)
                .aspects(aspects)
                .aspectSentiments(dbAspectSentiments)
                .overallSentiment(overallSentiment)
                .confidenceScore(Math.round(overallConfidence * 1000.0) / 1000.0)
                .build();

        analysis = analysisRepository.save(analysis);

        return AnalyzeResponse.builder()
                .analysisId(analysis.getId().toString())
                .contentId(contentId)
                .textPreview(text.length() > 200 ? text.substring(0, 200) : text)
                .aspectsAnalyzed(aspects)
                .aspectSentiments(aspectSentiments)
                .overallSentiment(OverallSentiment.builder()
                        .score(overallSentiment)
                        .label(getSentimentLabel(overallSentiment))
                        .build())
                .confidence(analysis.getConfidenceScore())
                .analyzedAt(LocalDateTime.now().toString())
                .build();
    }

    /**
     * 분석 히스토리 조회
     */
    @Transactional(readOnly = true)
    public HistoryResponse getAnalysisHistory(String contentId, int limit) {
        List<ABSAAnalysis> analyses = analysisRepository.findByContentIdOrderByCreatedAtDesc(contentId);
        
        List<HistoryItem> items = analyses.stream()
                .limit(limit)
                .map(analysis -> {
                    Map<String, AspectSentiment> sentiments = analysis.getAspectSentiments().entrySet().stream()
                            .collect(Collectors.toMap(
                                    Map.Entry::getKey,
                                    e -> AspectSentiment.builder()
                                            .sentimentScore(e.getValue().getSentimentScore())
                                            .sentimentLabel(e.getValue().getSentimentLabel())
                                            .confidence(e.getValue().getConfidence())
                                            .build()
                            ));
                    
                    return HistoryItem.builder()
                            .id(analysis.getId().toString())
                            .aspects(analysis.getAspects())
                            .aspectSentiments(sentiments)
                            .overallSentiment(analysis.getOverallSentiment())
                            .confidence(analysis.getConfidenceScore())
                            .analyzedAt(analysis.getCreatedAt() != null ? analysis.getCreatedAt().toString() : null)
                            .build();
                })
                .collect(Collectors.toList());

        return HistoryResponse.builder()
                .contentId(contentId)
                .analyses(items)
                .total(items.size())
                .limit(limit)
                .build();
    }

    /**
     * 배치 분석
     */
    @Transactional
    public BatchResponse batchAnalyze(List<AnalyzeRequest> requests) {
        List<Object> results = new ArrayList<>();
        int successCount = 0;
        int errorCount = 0;

        for (AnalyzeRequest request : requests) {
            try {
                AnalyzeResponse response = analyzeABSA(request);
                results.add(response);
                successCount++;
            } catch (Exception e) {
                errorCount++;
                Map<String, String> errorResult = new HashMap<>();
                errorResult.put("error", e.getMessage());
                errorResult.put("textPreview", request.getText() != null && request.getText().length() > 100 
                        ? request.getText().substring(0, 100) 
                        : request.getText());
                results.add(errorResult);
            }
        }

        return BatchResponse.builder()
                .results(results)
                .totalProcessed(requests.size())
                .successCount(successCount)
                .errorCount(errorCount)
                .build();
    }

    /**
     * 속성별 감성 점수 계산 (간단한 규칙 기반)
     */
    private double analyzeAspectSentiment(String text, String aspect) {
        String textLower = text.toLowerCase();
        String aspectLower = aspect.toLowerCase();

        List<String> positiveKeywords = Arrays.asList("좋다", "훌륭", "만족", "우수", "높은", "안정", "저렴");
        List<String> negativeKeywords = Arrays.asList("나쁘다", "불만", "부족", "높다", "비싸다", "불안");

        double score = 0.0;

        if (textLower.contains(aspectLower)) {
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

        return Math.max(-1.0, Math.min(1.0, score));
    }

    /**
     * 감성 점수를 레이블로 변환
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
