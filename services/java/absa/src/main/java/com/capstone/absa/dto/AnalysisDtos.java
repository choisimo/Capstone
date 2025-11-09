package com.capstone.absa.dto;

import jakarta.validation.constraints.*;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

/**
 * ABSA 분석 관련 DTO 클래스들
 * 
 * Python 모델의 Pydantic 스키마를 Java record로 변환한 것입니다.
 * Reference: BACKEND-ABSA-SERVICE/app/routers/analysis.py
 */
public class AnalysisDtos {

    /**
     * ABSA 분석 요청 DTO
     */
    public record AnalyzeRequest(
        @NotBlank(message = "Text is required")
        @Size(min = 1, max = 10000, message = "Text must be between 1 and 10000 characters")
        String text,

        List<String> aspects,  // Optional: 분석할 속성 리스트

        String contentId  // Optional: 컨텐츠 ID
    ) {}

    /**
     * 속성별 감성 결과 DTO
     */
    public record AspectSentiment(
        @NotNull
        Double sentimentScore,  // -1.0 ~ 1.0

        @NotBlank
        String sentimentLabel,  // positive, negative, neutral

        @NotNull
        @Min(0)
        @Max(1)
        Double confidence  // 0.0 ~ 1.0
    ) {}

    /**
     * 전체 감성 결과 DTO
     */
    public record OverallSentiment(
        @NotNull
        Double score,  // -1.0 ~ 1.0

        @NotBlank
        String label  // positive, negative, neutral
    ) {}

    /**
     * ABSA 분석 응답 DTO
     */
    public record AnalyzeResponse(
        @NotBlank
        String analysisId,

        @NotBlank
        String contentId,

        @NotBlank
        String textPreview,

        @NotNull
        List<String> aspectsAnalyzed,

        @NotNull
        Map<String, AspectSentiment> aspectSentiments,

        @NotNull
        OverallSentiment overallSentiment,

        @NotNull
        @Min(0)
        @Max(1)
        Double confidence,

        @NotBlank
        String analyzedAt
    ) {}

    /**
     * 분석 히스토리 아이템 DTO
     */
    public record HistoryItem(
        @NotBlank
        String id,

        @NotNull
        List<String> aspects,

        @NotNull
        Map<String, AspectSentiment> aspectSentiments,

        @NotNull
        Double overallSentiment,

        @NotNull
        Double confidence,

        String analyzedAt
    ) {}

    /**
     * 분석 히스토리 응답 DTO
     */
    public record HistoryResponse(
        @NotBlank
        String contentId,

        @NotNull
        List<HistoryItem> analyses,

        @NotNull
        @Min(0)
        Integer total,

        @NotNull
        @Min(1)
        Integer limit,

        @NotNull
        PaginationMeta pagination
    ) {}

    /**
     * 페이징 메타데이터 DTO
     */
    public record PaginationMeta(
        @NotNull
        @Min(0)
        Integer total,

        @NotNull
        @Min(1)
        Integer limit,

        @NotNull
        @Min(0)
        Integer offset
    ) {}

    /**
     * 배치 분석 결과 DTO
     */
    public record BatchAnalyzeResponse(
        @NotNull
        List<Object> results,  // AnalyzeResponse 또는 에러 메시지

        @NotNull
        @Min(0)
        Integer totalProcessed,

        @NotNull
        @Min(0)
        Integer successCount,

        @NotNull
        @Min(0)
        Integer errorCount
    ) {}

    /**
     * 배치 분석 에러 아이템 DTO
     */
    public record BatchErrorItem(
        @NotBlank
        String error,

        @NotBlank
        String textPreview
    ) {}
}
