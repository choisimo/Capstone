package com.capstone.absa.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

public class AnalysisDto {

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class AnalyzeRequest {
        private String text;
        private List<String> aspects;
        private String contentId;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class AspectSentiment {
        private Double sentimentScore;
        private String sentimentLabel;
        private Double confidence;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class OverallSentiment {
        private Double score;
        private String label;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class AnalyzeResponse {
        private String analysisId;
        private String contentId;
        private String textPreview;
        private List<String> aspectsAnalyzed;
        private Map<String, AspectSentiment> aspectSentiments;
        private OverallSentiment overallSentiment;
        private Double confidence;
        private String analyzedAt;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class HistoryItem {
        private String id;
        private List<String> aspects;
        private Map<String, AspectSentiment> aspectSentiments;
        private Double overallSentiment;
        private Double confidence;
        private String analyzedAt;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class HistoryResponse {
        private String contentId;
        private List<HistoryItem> analyses;
        private Integer total;
        private Integer limit;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class BatchResponse {
        private List<Object> results;
        private Integer totalProcessed;
        private Integer successCount;
        private Integer errorCount;
    }
}
