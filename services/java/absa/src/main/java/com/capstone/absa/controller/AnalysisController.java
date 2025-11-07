package com.capstone.absa.controller;

import com.capstone.absa.dto.AnalysisDtos.*;
import com.capstone.absa.service.AnalysisService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * ABSA 분석 컨트롤러
 * 
 * 속성 기반 감성 분석을 수행하는 API 엔드포인트를 제공합니다.
 * Reference: BACKEND-ABSA-SERVICE/app/routers/analysis.py
 */
@RestController
@RequestMapping("/api/v1/absa/analysis")
@RequiredArgsConstructor
@Slf4j
public class AnalysisController {

    private final AnalysisService analysisService;

    /**
     * 속성 기반 감성 분석 수행
     * 
     * POST /api/v1/absa/analysis/analyze
     * 
     * 텍스트와 속성 리스트를 받아 각 속성별 감성을 분석합니다.
     * 
     * @param request 분석 요청 {"text": "분석할 텍스트", "aspects": ["수익률", "안정성"], "content_id": "content-123"}
     * @return 속성별 감성 분석 결과
     */
    @PostMapping("/analyze")
    public ResponseEntity<AnalyzeResponse> analyzeABSA(@Valid @RequestBody AnalyzeRequest request) {
        log.info("POST /api/v1/absa/analysis/analyze - Analyze ABSA for text");
        
        AnalyzeResponse response = analysisService.analyzeABSA(request);
        
        return ResponseEntity.ok(response);
    }

    /**
     * 특정 컨텐츠의 ABSA 분석 히스토리 조회
     * 
     * GET /api/v1/absa/analysis/history/{contentId}
     * 
     * @param contentId 컨텐츠 ID
     * @param limit 조회할 최대 개수 (기본값: 10)
     * @return 분석 히스토리 목록
     */
    @GetMapping("/history/{contentId}")
    public ResponseEntity<HistoryResponse> getAnalysisHistory(
            @PathVariable String contentId,
            @RequestParam(defaultValue = "10") int limit) {
        log.info("GET /api/v1/absa/analysis/history/{} - Get analysis history (limit: {})", contentId, limit);
        
        HistoryResponse response = analysisService.getAnalysisHistory(contentId, limit);
        
        return ResponseEntity.ok(response);
    }

    /**
     * 배치 ABSA 분석
     * 
     * POST /api/v1/absa/analysis/batch
     * 
     * 여러 텍스트를 한 번에 분석합니다.
     * 
     * @param requests 분석 요청 리스트 [{"text": "텍스트1", "aspects": [...]}, {"text": "텍스트2", "aspects": [...]}]
     * @return 배치 분석 결과
     */
    @PostMapping("/batch")
    public ResponseEntity<BatchAnalyzeResponse> batchAnalyze(@Valid @RequestBody List<AnalyzeRequest> requests) {
        log.info("POST /api/v1/absa/analysis/batch - Batch analyze {} texts", requests.size());
        
        BatchAnalyzeResponse response = analysisService.batchAnalyze(requests);
        
        return ResponseEntity.ok(response);
    }
}
