package com.capstone.absa.dto;

import jakarta.validation.constraints.*;

import java.util.List;

/**
 * 속성(Aspect) 관련 DTO 클래스들
 * 
 * Python 모델의 Pydantic 스키마를 Java record로 변환한 것입니다.
 * Reference: BACKEND-ABSA-SERVICE/app/routers/aspects.py
 */
public class AspectDtos {

    /**
     * 속성 추출 요청 DTO
     */
    public record ExtractRequest(
        @NotBlank(message = "Text is required")
        @Size(min = 1, max = 10000, message = "Text must be between 1 and 10000 characters")
        String text
    ) {}

    /**
     * 추출된 속성 아이템 DTO
     */
    public record ExtractedAspect(
        @NotBlank
        String aspect,

        @NotNull
        @Min(0)
        @Max(1)
        Double confidence,

        @NotNull
        List<String> keywordsFound
    ) {}

    /**
     * 속성 추출 응답 DTO
     */
    public record ExtractResponse(
        @NotBlank
        String text,

        @NotNull
        List<ExtractedAspect> aspects,

        @NotNull
        @Min(0)
        Integer totalAspects,

        @NotBlank
        String modelVersion
    ) {}

    /**
     * 속성 아이템 DTO
     */
    public record AspectItem(
        @NotBlank
        String id,

        @NotBlank
        String name,

        String description,

        List<String> keywords,

        String modelVersion
    ) {}

    /**
     * 속성 목록 응답 DTO
     */
    public record AspectListResponse(
        @NotNull
        List<AspectItem> aspects,

        @NotNull
        @Min(0)
        Integer total,

        Integer limit,

        @NotNull
        @Min(0)
        Integer offset,

        PaginationMeta pagination
    ) {}

    /**
     * 속성 생성 요청 DTO
     */
    public record CreateAspectRequest(
        @NotBlank(message = "Name is required")
        @Size(min = 1, max = 255, message = "Name must be between 1 and 255 characters")
        String name,

        String description,

        List<String> keywords,

        String modelVersion
    ) {}

    /**
     * 속성 생성 응답 DTO
     */
    public record CreateAspectResponse(
        @NotBlank
        String id,

        @NotBlank
        String name,

        String description,

        List<String> keywords,

        String createdAt
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
}
