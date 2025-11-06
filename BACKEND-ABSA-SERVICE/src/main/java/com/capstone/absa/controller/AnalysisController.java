package com.capstone.absa.controller;

import com.capstone.absa.dto.AnalysisDto.*;
import com.capstone.absa.service.ABSAAnalysisService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * ABSA 분석 컨트롤러
 * 속성 기반 감성 분석을 수행하는 API 엔드포인트
 */
@RestController
@RequestMapping("/analysis")
@RequiredArgsConstructor
public class AnalysisController {

    private final ABSAAnalysisService analysisService;

    /**
     * 속성 기반 감성 분석 수행
     */
    @PostMapping("/analyze")
    public ResponseEntity<AnalyzeResponse> analyze(@RequestBody AnalyzeRequest request) {
        AnalyzeResponse response = analysisService.analyzeABSA(request);
        return ResponseEntity.ok(response);
    }

    /**
     * 분석 히스토리 조회
     */
    @GetMapping("/history/{contentId}")
    public ResponseEntity<HistoryResponse> getHistory(
            @PathVariable String contentId,
            @RequestParam(defaultValue = "10") int limit) {
        HistoryResponse response = analysisService.getAnalysisHistory(contentId, limit);
        return ResponseEntity.ok(response);
    }

    /**
     * 배치 분석
     */
    @PostMapping("/batch")
    public ResponseEntity<BatchResponse> batchAnalyze(@RequestBody List<AnalyzeRequest> requests) {
        BatchResponse response = analysisService.batchAnalyze(requests);
        return ResponseEntity.ok(response);
    }
}
