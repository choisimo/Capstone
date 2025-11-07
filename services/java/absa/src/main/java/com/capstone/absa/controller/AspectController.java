package com.capstone.absa.controller;

import com.capstone.absa.dto.AspectDtos.*;
import com.capstone.absa.service.AspectService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * 속성(Aspect) 추출 컨트롤러
 * 
 * 텍스트에서 분석할 속성(aspects)을 추출하는 API 엔드포인트를 제공합니다.
 * Reference: BACKEND-ABSA-SERVICE/app/routers/aspects.py
 */
@RestController
@RequestMapping("/api/v1/absa/aspects")
@RequiredArgsConstructor
@Slf4j
public class AspectController {

    private final AspectService aspectService;

    /**
     * 텍스트에서 속성 추출
     * 
     * POST /api/v1/absa/aspects/extract
     * 
     * @param request 속성 추출 요청 {"text": "분석할 텍스트"}
     * @return 추출된 속성 리스트와 신뢰도
     */
    @PostMapping("/extract")
    public ResponseEntity<ExtractResponse> extractAspects(@Valid @RequestBody ExtractRequest request) {
        log.info("POST /api/v1/absa/aspects/extract - Extract aspects from text");
        
        ExtractResponse response = aspectService.extractAspects(request);
        
        return ResponseEntity.ok(response);
    }

    /**
     * 사용 가능한 속성 목록 조회
     * 
     * GET /api/v1/absa/aspects/list
     * 
     * @return 활성화된 속성 모델 목록
     */
    @GetMapping("/list")
    public ResponseEntity<AspectListResponse> listAspects() {
        log.info("GET /api/v1/absa/aspects/list - List active aspects");
        
        AspectListResponse response = aspectService.listActiveAspects();
        
        return ResponseEntity.ok(response);
    }

    /**
     * 새로운 속성 모델 생성
     * 
     * POST /api/v1/absa/aspects/create
     * 
     * @param request 속성 생성 요청
     * @return 생성된 속성 정보
     */
    @PostMapping("/create")
    public ResponseEntity<CreateAspectResponse> createAspect(@Valid @RequestBody CreateAspectRequest request) {
        log.info("POST /api/v1/absa/aspects/create - Create new aspect: {}", request.name());
        
        try {
            CreateAspectResponse response = aspectService.createAspect(request);
            return ResponseEntity.ok(response);
        } catch (IllegalArgumentException e) {
            log.error("Failed to create aspect: {}", e.getMessage());
            return ResponseEntity.badRequest().build();
        }
    }
}
