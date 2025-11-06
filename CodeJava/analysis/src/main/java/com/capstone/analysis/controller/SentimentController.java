package com.capstone.analysis.controller;

import com.capstone.analysis.dto.SentimentDtos.*;
import com.capstone.analysis.service.SentimentService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

import static org.springframework.http.HttpStatus.INTERNAL_SERVER_ERROR;
import static org.springframework.http.HttpStatus.NOT_FOUND;

/**
 * 감성 분석 API 컨트롤러
 * 
 * 텍스트의 감성(긍정/부정/중립)을 분석하는 REST API를 제공합니다.
 * 개별 분석, 배치 처리, 히스토리 조회, 통계 제공 기능을 포함합니다.
 */
@RestController
@RequestMapping("/api/v1/sentiment")
public class SentimentController {
    
    private final SentimentService sentimentService;
    
    /**
     * 생성자 주입을 통한 의존성 주입
     * 
     * @param sentimentService 감성 분석 서비스
     */
    public SentimentController(SentimentService sentimentService) {
        this.sentimentService = sentimentService;
    }
    
    /**
     * 단일 텍스트 감성 분석
     * 
     * 입력된 텍스트의 감성을 분석하여 긍정/부정/중립으로 분류합니다.
     * 감성 점수(-1~1)와 신뢰도를 함께 반환합니다.
     * 
     * @param request 분석 요청 데이터 (텍스트, 컨텐츠 ID)
     * @return SentimentAnalysisResponse 분석 결과
     */
    @PostMapping("/analyze")
    public ResponseEntity<SentimentAnalysisResponse> analyzeSentiment(
            @RequestBody SentimentAnalysisRequest request) {
        try {
            SentimentAnalysisResponse response = sentimentService.analyzeSentiment(
                    request.text(), 
                    request.content_id()
            );
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to analyze sentiment: " + e.getMessage(), 
                    e
            );
        }
    }
    
    /**
     * 배치 감성 분석
     * 
     * 여러 텍스트를 동시에 분석합니다.
     * 대량의 텍스트 처리시 효율적이며, 백그라운드 작업으로 수행됩니다.
     * 
     * @param request 배치 분석 요청 데이터 (텍스트 목록)
     * @return BatchSentimentResponse 배치 처리 결과 및 통계
     */
    @PostMapping("/batch")
    public ResponseEntity<BatchSentimentResponse> batchAnalyzeSentiment(
            @RequestBody BatchSentimentRequest request) {
        try {
            BatchSentimentResponse response = sentimentService.batchAnalyzeSentiment(
                    request.texts()
            );
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to perform batch sentiment analysis: " + e.getMessage(), 
                    e
            );
        }
    }
    
    /**
     * 감성 분석 히스토리 조회
     * 
     * 특정 컨텐츠에 대한 과거 감성 분석 기록을 조회합니다.
     * 시간 순으로 정렬되어 반환됩니다.
     * 
     * @param contentId 컨텐츠 ID
     * @param limit 조회할 최대 개수 (기본: 10)
     * @return List<SentimentHistory> 감성 분석 히스토리 목록
     */
    @GetMapping("/history/{contentId}")
    public ResponseEntity<List<SentimentHistory>> getSentimentHistory(
            @PathVariable String contentId,
            @RequestParam(defaultValue = "10") int limit) {
        try {
            List<SentimentHistory> history = sentimentService.getSentimentHistory(
                    contentId, 
                    limit
            );
            
            if (history.isEmpty()) {
                throw new ResponseStatusException(
                        NOT_FOUND, 
                        "No sentiment history found for content_id: " + contentId
                );
            }
            
            return ResponseEntity.ok(history);
        } catch (ResponseStatusException e) {
            throw e;
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to retrieve sentiment history: " + e.getMessage(), 
                    e
            );
        }
    }
    
    /**
     * 감성 분석 통계 조회
     * 
     * 지정된 기간 동안의 감성 분석 통계를 제공합니다.
     * 전체 긍정/부정/중립 비율, 평균 신뢰도 등의 정보를 포함합니다.
     * 
     * @param startDate 시작 날짜 (YYYY-MM-DD 형식, 선택)
     * @param endDate 종료 날짜 (YYYY-MM-DD 형식, 선택)
     * @return SentimentStats 감성 분석 통계 데이터
     */
    @GetMapping("/stats")
    public ResponseEntity<SentimentStats> getSentimentStats(
            @RequestParam(required = false) String startDate,
            @RequestParam(required = false) String endDate) {
        try {
            SentimentStats stats = sentimentService.getSentimentStatistics(
                    startDate, 
                    endDate
            );
            return ResponseEntity.ok(stats);
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to retrieve sentiment statistics: " + e.getMessage(), 
                    e
            );
        }
    }
}
