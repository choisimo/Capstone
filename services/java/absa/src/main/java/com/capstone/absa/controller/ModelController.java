package com.capstone.absa.controller;

import com.capstone.absa.dto.ModelDtos.*;
import com.capstone.absa.service.ModelService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * ABSA 모델 관리 컨트롤러
 * 
 * ABSA 모델의 생성, 조회, 업데이트, 삭제를 관리하는 API 엔드포인트를 제공합니다.
 * Reference: BACKEND-ABSA-SERVICE/app/routers/models.py
 */
@RestController
@RequestMapping("/api/v1/absa/models")
@RequiredArgsConstructor
@Slf4j
public class ModelController {

    private final ModelService modelService;

    /**
     * ABSA 모델 목록 조회
     * 
     * GET /api/v1/absa/models/
     * 
     * @param skip 건너뛸 개수 (기본값: 0)
     * @param limit 조회할 최대 개수 (기본값: 10)
     * @return 모델 목록과 메타데이터
     */
    @GetMapping("/")
    public ResponseEntity<ModelListResponse> listModels(
            @RequestParam(defaultValue = "0") int skip,
            @RequestParam(defaultValue = "10") int limit) {
        log.info("GET /api/v1/absa/models/ - List models (skip: {}, limit: {})", skip, limit);
        
        ModelListResponse response = modelService.listModels(skip, limit);
        
        return ResponseEntity.ok(response);
    }

    /**
     * 특정 ABSA 모델 상세 조회
     * 
     * GET /api/v1/absa/models/{modelId}
     * 
     * @param modelId 모델 ID
     * @return 모델 상세 정보
     */
    @GetMapping("/{modelId}")
    public ResponseEntity<ModelDetailResponse> getModel(@PathVariable String modelId) {
        log.info("GET /api/v1/absa/models/{} - Get model details", modelId);
        
        try {
            ModelDetailResponse response = modelService.getModel(modelId);
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            log.error("Model not found: {}", modelId);
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * ABSA 모델 업데이트
     * 
     * PUT /api/v1/absa/models/{modelId}
     * 
     * @param modelId 모델 ID
     * @param request 업데이트할 데이터
     * @return 업데이트된 모델 정보
     */
    @PutMapping("/{modelId}")
    public ResponseEntity<ModelUpdateResponse> updateModel(
            @PathVariable String modelId,
            @Valid @RequestBody ModelUpdateRequest request) {
        log.info("PUT /api/v1/absa/models/{} - Update model", modelId);
        
        try {
            ModelUpdateResponse response = modelService.updateModel(modelId, request);
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            log.error("Model not found: {}", modelId);
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * ABSA 모델 삭제
     * 
     * DELETE /api/v1/absa/models/{modelId}
     * 
     * @param modelId 모델 ID
     * @return 삭제 결과
     */
    @DeleteMapping("/{modelId}")
    public ResponseEntity<DeleteResponse> deleteModel(@PathVariable String modelId) {
        log.info("DELETE /api/v1/absa/models/{} - Delete model", modelId);
        
        try {
            DeleteResponse response = modelService.deleteModel(modelId);
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            log.error("Model not found: {}", modelId);
            return ResponseEntity.notFound().build();
        }
    }

    /**
     * 기본 ABSA 모델 초기화
     * 
     * POST /api/v1/absa/models/initialize
     * 
     * 연금 관련 기본 속성 모델을 생성합니다.
     * 
     * @return 초기화 결과 (생성된 모델 목록, 건너뛴 모델 목록)
     */
    @PostMapping("/initialize")
    public ResponseEntity<InitializeResponse> initializeDefaultModels() {
        log.info("POST /api/v1/absa/models/initialize - Initialize default models");
        
        InitializeResponse response = modelService.initializeDefaultModels();
        
        return ResponseEntity.ok(response);
    }
}
