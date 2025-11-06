package com.capstone.analysis.controller;

import com.capstone.analysis.dto.ModelDtos.*;
import com.capstone.analysis.service.MLModelService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.Map;

import static org.springframework.http.HttpStatus.INTERNAL_SERVER_ERROR;
import static org.springframework.http.HttpStatus.NOT_FOUND;

/**
 * ML 모델 관리 API 컨트롤러
 * 
 * 기계학습 모델의 업로드, 학습, 관리를 담당하는 REST API를 제공합니다.
 * 모델 버전 관리, A/B 테스트, 학습 모니터링 기능을 제공합니다.
 */
@RestController
@RequestMapping("/api/v1/models")
public class ModelController {
    
    private final MLModelService mlModelService;
    
    /**
     * 생성자 주입을 통한 의존성 주입
     * 
     * @param mlModelService ML 모델 서비스
     */
    public ModelController(MLModelService mlModelService) {
        this.mlModelService = mlModelService;
    }
    
    /**
     * ML 모델 업로드
     * 
     * 학습된 ML 모델을 서비스에 등록합니다.
     * 모델 파일과 메타데이터를 저장하고 버전을 관리합니다.
     * 
     * @param request 모델 등록 요청 데이터 (이름, 타입, 경로, 메트릭)
     * @return MLModelResponse 등록된 모델 정보
     */
    @PostMapping("/upload")
    public ResponseEntity<MLModelResponse> uploadModel(
            @RequestBody MLModelRequest request) {
        try {
            MLModelResponse response = mlModelService.uploadModel(request);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to upload model: " + e.getMessage(), 
                    e
            );
        }
    }
    
    /**
     * 모델 목록 조회
     * 
     * 등록된 모든 ML 모델의 목록을 조회합니다.
     * 타입별 필터링과 활성 모델만 조회하는 옵션을 제공합니다.
     * 
     * @param modelType 모델 타입 필터 (sentiment/classification)
     * @param activeOnly 활성 모델만 조회 여부 (기본: false)
     * @return List<MLModelResponse> 모델 목록
     */
    @GetMapping
    public ResponseEntity<List<MLModelResponse>> listModels(
            @RequestParam(required = false) String modelType,
            @RequestParam(defaultValue = "false") boolean activeOnly) {
        try {
            List<MLModelResponse> models = mlModelService.listModels(
                    modelType, 
                    activeOnly
            );
            return ResponseEntity.ok(models);
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to retrieve model list: " + e.getMessage(), 
                    e
            );
        }
    }
    
    /**
     * 특정 모델 조회
     * 
     * ID를 통해 특정 ML 모델의 상세 정보를 조회합니다.
     * 
     * @param modelId 모델 ID
     * @return MLModelResponse 모델 상세 정보
     */
    @GetMapping("/{modelId}")
    public ResponseEntity<MLModelResponse> getModel(
            @PathVariable Long modelId) {
        try {
            MLModelResponse model = mlModelService.getModel(modelId);
            
            if (model == null) {
                throw new ResponseStatusException(
                        NOT_FOUND, 
                        "Model not found with ID: " + modelId
                );
            }
            
            return ResponseEntity.ok(model);
        } catch (ResponseStatusException e) {
            throw e;
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to retrieve model: " + e.getMessage(), 
                    e
            );
        }
    }
    
    /**
     * 모델 활성화
     * 
     * 특정 모델을 활성화하여 실제 서비스에서 사용하도록 설정합니다.
     * 기존 활성 모델은 자동으로 비활성화됩니다.
     * 
     * @param modelId 활성화할 모델 ID
     * @return Map<String, String> 활성화 성공 메시지
     */
    @PutMapping("/{modelId}/activate")
    public ResponseEntity<Map<String, String>> activateModel(
            @PathVariable Long modelId) {
        try {
            boolean success = mlModelService.activateModel(modelId);
            
            if (!success) {
                throw new ResponseStatusException(
                        NOT_FOUND, 
                        "Model not found with ID: " + modelId
                );
            }
            
            return ResponseEntity.ok(Map.of("message", "Model activated successfully"));
        } catch (ResponseStatusException e) {
            throw e;
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to activate model: " + e.getMessage(), 
                    e
            );
        }
    }
    
    /**
     * 모델 학습
     * 
     * 새로운 ML 모델을 학습시킵니다.
     * 학습 작업은 백그라운드에서 비동기로 수행됩니다.
     * 
     * @param request 모델 학습 요청 데이터 (모델명, 데이터 경로, 하이퍼파라미터)
     * @return ModelTrainingResponse 학습 작업 정보
     */
    @PostMapping("/train")
    public ResponseEntity<ModelTrainingResponse> trainModel(
            @RequestBody ModelTrainingRequest request) {
        try {
            ModelTrainingResponse response = mlModelService.trainModel(request);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to start model training: " + e.getMessage(), 
                    e
            );
        }
    }
    
    /**
     * 학습 상태 확인
     * 
     * 진행 중인 모델 학습 작업의 상태를 확인합니다.
     * 
     * @param jobId 학습 작업 ID
     * @return TrainingStatus 학습 상태 정보 (status, progress, metrics)
     */
    @GetMapping("/training/{jobId}")
    public ResponseEntity<TrainingStatus> getTrainingStatus(
            @PathVariable String jobId) {
        try {
            TrainingStatus status = mlModelService.getTrainingStatus(jobId);
            
            if (status == null) {
                throw new ResponseStatusException(
                        NOT_FOUND, 
                        "Training job not found with ID: " + jobId
                );
            }
            
            return ResponseEntity.ok(status);
        } catch (ResponseStatusException e) {
            throw e;
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to retrieve training status: " + e.getMessage(), 
                    e
            );
        }
    }
    
    /**
     * 모델 삭제
     * 
     * 지정된 ML 모델을 삭제합니다.
     * 활성 상태의 모델은 삭제할 수 없습니다.
     * 
     * @param modelId 삭제할 모델 ID
     * @return Map<String, String> 삭제 성공 메시지
     */
    @DeleteMapping("/{modelId}")
    public ResponseEntity<Map<String, String>> deleteModel(
            @PathVariable Long modelId) {
        try {
            boolean success = mlModelService.deleteModel(modelId);
            
            if (!success) {
                throw new ResponseStatusException(
                        NOT_FOUND, 
                        "Model not found with ID: " + modelId
                );
            }
            
            return ResponseEntity.ok(Map.of("message", "Model deleted successfully"));
        } catch (ResponseStatusException e) {
            throw e;
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to delete model: " + e.getMessage(), 
                    e
            );
        }
    }
}
