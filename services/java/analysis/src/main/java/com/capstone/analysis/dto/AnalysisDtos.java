package com.capstone.analysis.dto;

import java.time.OffsetDateTime;
import java.util.List;

/**
 * Unified DTO definitions for reporting analysis results across SENTIMENT, ABSA,
 * and future ML analysis types.
 */
public class AnalysisDtos {

    /**
     * Supported analysis types. Extend this enum as new analysis capabilities are added.
     */
    public enum AnalysisType {
        SENTIMENT,
        ABSA
        // FUTURE: TOXICITY, TOPIC_MODELING, etc.
    }

    /**
     * Filter payload accepted by the Analysis Report API.
     */
    public record AnalysisReportFilter(
            List<AnalysisType> analysisTypes,
            List<String> modelTypes,
            String dateFrom,
            String dateTo,
            List<String> aspects,
            List<String> labels,
            List<String> sources,
            Double minScore
    ) {}

    /**
     * Canonical analysis record representing a single "text + aspect" evaluation row.
     */
    public record AnalysisRecord(
            Long analysisId,
            AnalysisType analysisType,
            String contentId,
            String text,
            String aspect,
            String trueLabel,
            String predictedLabel,
            Double score,
            String modelType,
            String modelVersion,
            String trainingJobId,
            OffsetDateTime analyzedAt,
            String source,
            List<String> tags
    ) {}

    /**
     * Aggregate statistics summarizing a filtered result set.
     */
    public record AnalysisSummary(
            long totalCount,
            long positiveCount,
            long negativeCount,
            long neutralCount,
            double averageScore
    ) {}

    /**
     * Report response payload delivered to API consumers.
     */
    public record AnalysisReportResponse(
            AnalysisReportFilter filter,
            AnalysisSummary summary,
            List<AnalysisRecord> details
    ) {}
}
