package com.capstone.absa.service;

import com.capstone.absa.dto.AspectDtos.*;
import com.capstone.absa.entity.AspectModelEntity;
import com.capstone.absa.repository.AspectModelRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * 속성(Aspect) 추출 서비스
 * 
 * 텍스트에서 분석 대상 속성을 추출하는 비즈니스 로직을 처리합니다.
 * Reference: BACKEND-ABSA-SERVICE/app/routers/aspects.py
 */
@Service
@RequiredArgsConstructor
@Slf4j
@Transactional(readOnly = true)
public class AspectService {

    private final AspectModelRepository aspectModelRepository;

    /**
     * 텍스트에서 속성 추출
     * 
     * 활성화된 속성 모델의 키워드를 사용하여 텍스트에서 속성을 추출합니다.
     * 
     * @param request 속성 추출 요청
     * @return 추출된 속성 리스트
     */
    public ExtractResponse extractAspects(ExtractRequest request) {
        log.info("Extracting aspects from text: {}", request.text().substring(0, Math.min(100, request.text().length())));
        
        String text = request.text();
        List<AspectModelEntity> activeAspects = aspectModelRepository.findByIsActive(1);
        
        List<ExtractedAspect> extractedAspects = new ArrayList<>();
        
        // 각 활성화된 속성 모델에 대해 키워드 매칭 수행
        for (AspectModelEntity aspectModel : activeAspects) {
            List<String> keywords = aspectModel.getKeywords();
            if (keywords == null || keywords.isEmpty()) {
                continue;
            }
            
            // 텍스트에 키워드가 포함되어 있는지 확인
            List<String> foundKeywords = new ArrayList<>();
            for (String keyword : keywords) {
                if (text.toLowerCase().contains(keyword.toLowerCase())) {
                    foundKeywords.add(keyword);
                }
            }
            
            // 키워드가 발견된 경우 속성 추가
            if (!foundKeywords.isEmpty()) {
                double confidence = 0.85; // 임시 신뢰도
                extractedAspects.add(new ExtractedAspect(
                    aspectModel.getName(),
                    confidence,
                    foundKeywords
                ));
            }
        }
        
        // 기본 속성 추가 (키워드 매칭 실패 시)
        if (extractedAspects.isEmpty()) {
            List<String> defaultAspects = List.of("수익률", "안정성", "관리비용", "가입조건");
            for (String aspect : defaultAspects) {
                if (text.length() > 20) { // 텍스트가 충분히 긴 경우
                    extractedAspects.add(new ExtractedAspect(
                        aspect,
                        0.7,
                        List.of()
                    ));
                }
            }
        }
        
        log.info("Extracted {} aspects from text", extractedAspects.size());
        
        return new ExtractResponse(
            text.substring(0, Math.min(200, text.length())),
            extractedAspects,
            extractedAspects.size(),
            "v1.0.0"
        );
    }

    /**
     * 활성화된 속성 모델 목록 조회
     * 
     * @return 활성화된 속성 모델 리스트
     */
    public AspectListResponse listActiveAspects() {
        log.info("Listing active aspect models");
        
        List<AspectModelEntity> activeAspects = aspectModelRepository.findByIsActive(1);
        
        List<AspectItem> items = activeAspects.stream()
            .map(aspect -> new AspectItem(
                aspect.getId(),
                aspect.getName(),
                aspect.getDescription(),
                aspect.getKeywords(),
                aspect.getModelVersion()
            ))
            .toList();
        
        log.info("Found {} active aspect models", items.size());
        
        return new AspectListResponse(
            items,
            items.size(),
            null,
            0,
            null
        );
    }

    /**
     * 새로운 속성 모델 생성
     * 
     * @param request 속성 생성 요청
     * @return 생성된 속성 정보
     * @throws IllegalArgumentException 이미 존재하는 속성 이름인 경우
     */
    @Transactional
    public CreateAspectResponse createAspect(CreateAspectRequest request) {
        log.info("Creating new aspect model: {}", request.name());
        
        // 중복 확인
        if (aspectModelRepository.existsByName(request.name())) {
            log.error("Aspect already exists: {}", request.name());
            throw new IllegalArgumentException("Aspect already exists: " + request.name());
        }
        
        // 새 속성 모델 생성
        AspectModelEntity newAspect = AspectModelEntity.builder()
            .id(UUID.randomUUID().toString())
            .name(request.name())
            .description(request.description())
            .keywords(request.keywords() != null ? request.keywords() : List.of())
            .modelVersion(request.modelVersion() != null ? request.modelVersion() : "v1.0.0")
            .isActive(1)
            .build();
        
        AspectModelEntity saved = aspectModelRepository.save(newAspect);
        
        log.info("Created aspect model with ID: {}", saved.getId());
        
        return new CreateAspectResponse(
            saved.getId(),
            saved.getName(),
            saved.getDescription(),
            saved.getKeywords(),
            saved.getCreatedAt() != null ? saved.getCreatedAt().toString() : null
        );
    }
}
