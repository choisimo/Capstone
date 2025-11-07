package com.capstone.absa.service;

import com.capstone.absa.dto.ModelDtos.*;
import com.capstone.absa.entity.AspectModelEntity;
import com.capstone.absa.repository.AspectModelRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * ABSA 모델 관리 서비스
 * 
 * ABSA 모델의 CRUD 작업을 처리하는 비즈니스 로직입니다.
 * Reference: BACKEND-ABSA-SERVICE/app/routers/models.py
 */
@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class ModelService {

    private final AspectModelRepository modelRepository;

    /**
     * ABSA 모델 목록 조회
     * 
     * @param skip 건너뛸 개수
     * @param limit 조회할 최대 개수
     * @return 모델 목록과 메타데이터
     */
    public ModelListResponse listModels(int skip, int limit) {
        log.info("Listing models with skip={}, limit={}", skip, limit);
        
        int page = skip / limit;
        PageRequest pageRequest = PageRequest.of(page, limit);
        Page<AspectModelEntity> modelsPage = modelRepository.findAll(pageRequest);
        
        List<ModelItem> items = modelsPage.getContent().stream()
            .map(model -> new ModelItem(
                model.getId(),
                model.getName(),
                model.getDescription(),
                model.getModelVersion(),
                model.getIsActive(),
                model.getCreatedAt() != null ? model.getCreatedAt().toString() : null
            ))
            .toList();
        
        long total = modelsPage.getTotalElements();
        
        log.info("Found {} models (total: {})", items.size(), total);
        
        return new ModelListResponse(
            items,
            (int) total,
            skip,
            limit,
            new PaginationMeta((int) total, limit, skip)
        );
    }

    /**
     * 특정 ABSA 모델 상세 조회
     * 
     * @param modelId 모델 ID
     * @return 모델 상세 정보
     * @throws IllegalArgumentException 모델을 찾을 수 없는 경우
     */
    public ModelDetailResponse getModel(String modelId) {
        log.info("Getting model details for ID: {}", modelId);
        
        AspectModelEntity model = modelRepository.findById(modelId)
            .orElseThrow(() -> {
                log.error("Model not found: {}", modelId);
                return new IllegalArgumentException("Model not found: " + modelId);
            });
        
        return new ModelDetailResponse(
            model.getId(),
            model.getName(),
            model.getDescription(),
            model.getKeywords(),
            model.getModelVersion(),
            model.getIsActive(),
            model.getCreatedAt() != null ? model.getCreatedAt().toString() : null,
            model.getUpdatedAt() != null ? model.getUpdatedAt().toString() : null
        );
    }

    /**
     * ABSA 모델 업데이트
     * 
     * @param modelId 모델 ID
     * @param request 업데이트 요청
     * @return 업데이트된 모델 정보
     * @throws IllegalArgumentException 모델을 찾을 수 없는 경우
     */
    @Transactional
    public ModelUpdateResponse updateModel(String modelId, ModelUpdateRequest request) {
        log.info("Updating model: {}", modelId);
        
        AspectModelEntity model = modelRepository.findById(modelId)
            .orElseThrow(() -> {
                log.error("Model not found: {}", modelId);
                return new IllegalArgumentException("Model not found: " + modelId);
            });
        
        // 업데이트 가능한 필드만 변경
        if (request.name() != null) {
            model.setName(request.name());
        }
        if (request.description() != null) {
            model.setDescription(request.description());
        }
        if (request.keywords() != null) {
            model.setKeywords(request.keywords());
        }
        if (request.modelVersion() != null) {
            model.setModelVersion(request.modelVersion());
        }
        if (request.isActive() != null) {
            model.setIsActive(request.isActive());
        }
        
        AspectModelEntity updated = modelRepository.save(model);
        
        log.info("Model updated: {}", modelId);
        
        return new ModelUpdateResponse(
            updated.getId(),
            updated.getName(),
            updated.getDescription(),
            updated.getKeywords(),
            updated.getModelVersion(),
            updated.getIsActive(),
            updated.getUpdatedAt() != null ? updated.getUpdatedAt().toString() : null
        );
    }

    /**
     * ABSA 모델 삭제
     * 
     * @param modelId 모델 ID
     * @return 삭제 결과
     * @throws IllegalArgumentException 모델을 찾을 수 없는 경우
     */
    @Transactional
    public DeleteResponse deleteModel(String modelId) {
        log.info("Deleting model: {}", modelId);
        
        AspectModelEntity model = modelRepository.findById(modelId)
            .orElseThrow(() -> {
                log.error("Model not found: {}", modelId);
                return new IllegalArgumentException("Model not found: " + modelId);
            });
        
        String modelName = model.getName();
        modelRepository.delete(model);
        
        log.info("Model deleted: {} ({})", modelName, modelId);
        
        return new DeleteResponse(
            "Model '" + modelName + "' deleted successfully",
            modelId
        );
    }

    /**
     * 기본 ABSA 모델 초기화
     * 
     * 연금 관련 기본 속성 모델을 생성합니다.
     * 
     * @return 초기화 결과
     */
    @Transactional
    public InitializeResponse initializeDefaultModels() {
        log.info("Initializing default ABSA models");
        
        List<DefaultAspectData> defaultAspects = List.of(
            new DefaultAspectData("수익률", "투자 수익률 및 수익성 관련 속성",
                List.of("수익", "이익", "수익률", "수익성", "투자수익", "운용수익")),
            new DefaultAspectData("안정성", "연금 운용의 안정성 및 신뢰성",
                List.of("안정", "신뢰", "보장", "안전", "리스크", "위험")),
            new DefaultAspectData("관리비용", "관리 수수료 및 비용 관련",
                List.of("수수료", "비용", "관리비", "운용비", "비용부담", "수수료율")),
            new DefaultAspectData("가입조건", "가입 자격 및 조건",
                List.of("가입", "자격", "조건", "요건", "신청", "가입절차")),
            new DefaultAspectData("서비스", "고객 서비스 및 지원",
                List.of("서비스", "상담", "지원", "고객", "응대", "안내"))
        );
        
        List<String> createdModels = new ArrayList<>();
        List<String> skippedModels = new ArrayList<>();
        
        for (DefaultAspectData aspectData : defaultAspects) {
            // 중복 확인
            if (modelRepository.existsByName(aspectData.name())) {
                skippedModels.add(aspectData.name());
                log.info("Skipping existing model: {}", aspectData.name());
                continue;
            }
            
            // 새 모델 생성
            AspectModelEntity model = AspectModelEntity.builder()
                .id(UUID.randomUUID().toString())
                .name(aspectData.name())
                .description(aspectData.description())
                .keywords(aspectData.keywords())
                .modelVersion("v1.0.0")
                .isActive(1)
                .build();
            
            modelRepository.save(model);
            createdModels.add(aspectData.name());
            log.info("Created model: {}", aspectData.name());
        }
        
        log.info("Initialization completed: {} created, {} skipped", createdModels.size(), skippedModels.size());
        
        return new InitializeResponse(
            createdModels,
            skippedModels,
            createdModels.size(),
            skippedModels.size()
        );
    }

    /**
     * 기본 속성 데이터를 나타내는 내부 레코드
     */
    private record DefaultAspectData(
        String name,
        String description,
        List<String> keywords
    ) {}
}
