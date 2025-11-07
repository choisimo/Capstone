package com.capstone.absa.dto;

import jakarta.validation.constraints.*;

import java.util.List;

/**
 * ABSA 모델 관련 DTO 클래스들
 * 
 * Python 모델의 Pydantic 스키마를 Java record로 변환한 것입니다.
 * Reference: BACKEND-ABSA-SERVICE/app/routers/models.py
 */
public class ModelDtos {

    /**
     * 모델 아이템 DTO
     */
    public record ModelItem(
        @NotBlank
        String id,

        @NotBlank
        String name,

        String description,

        String modelVersion,

        @NotNull
        Integer isActive,  // 1: 활성, 0: 비활성

        String createdAt
    ) {}

    /**
     * 모델 목록 응답 DTO
     */
    public record ModelListResponse(
        @NotNull
        List<ModelItem> models,

        @NotNull
        @Min(0)
        Integer total,

        @NotNull
        @Min(0)
        Integer skip,

        @NotNull
        @Min(1)
        Integer limit,

        @NotNull
        PaginationMeta pagination
    ) {}

    /**
     * 모델 상세 응답 DTO
     */
    public record ModelDetailResponse(
        @NotBlank
        String id,

        @NotBlank
        String name,

        String description,

        List<String> keywords,

        String modelVersion,

        @NotNull
        Integer isActive,

        String createdAt,

        String updatedAt
    ) {}

    /**
     * 모델 업데이트 요청 DTO
     */
    public record ModelUpdateRequest(
        String name,

        String description,

        List<String> keywords,

        String modelVersion,

        Integer isActive  // 1: 활성, 0: 비활성
    ) {}

    /**
     * 모델 업데이트 응답 DTO
     */
    public record ModelUpdateResponse(
        @NotBlank
        String id,

        @NotBlank
        String name,

        String description,

        List<String> keywords,

        String modelVersion,

        @NotNull
        Integer isActive,

        String updatedAt
    ) {}

    /**
     * 모델 삭제 응답 DTO
     */
    public record DeleteResponse(
        @NotBlank
        String message,

        @NotBlank
        String deletedId
    ) {}

    /**
     * 모델 초기화 응답 DTO
     */
    public record InitializeResponse(
        @NotNull
        List<String> created,

        @NotNull
        List<String> skipped,

        @NotNull
        @Min(0)
        Integer totalCreated,

        @NotNull
        @Min(0)
        Integer totalSkipped
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
