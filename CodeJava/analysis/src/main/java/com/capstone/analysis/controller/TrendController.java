package com.capstone.analysis.controller;

import com.capstone.analysis.dto.TrendDtos.*;
import com.capstone.analysis.service.TrendService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

import static org.springframework.http.HttpStatus.INTERNAL_SERVER_ERROR;
import static org.springframework.http.HttpStatus.NOT_FOUND;

/**
 * 트렌드 분석 API 컨트롤러
 * 
 * 시간에 따른 감성 및 볼륨 트렌드를 분석하는 REST API를 제공합니다.
 * 일별, 주별, 월별 트렌드 분석과 인기 키워드 추출 기능을 제공합니다.
 */
@RestController
@RequestMapping("/api/v1/trends")
public class TrendController {
    
    private final TrendService trendService;
    
    /**
     * 생성자 주입을 통한 의존성 주입
     * 
     * @param trendService 트렌드 분석 서비스
     */
    public TrendController(TrendService trendService) {
        this.trendService = trendService;
    }
    
    /**
     * 트렌드 분석 수행
     * 
     * 지정된 기간과 대상에 대한 트렌드를 분석합니다.
     * 감성 변화 추이, 볼륨 트렌드, 주요 키워드를 추출합니다.
     * 
     * @param request 트렌드 분석 요청 데이터 (기간, 대상, 날짜 범위)
     * @return TrendAnalysisResponse 트렌드 분석 결과
     */
    @PostMapping("/analyze")
    public ResponseEntity<TrendAnalysisResponse> analyzeTrends(
            @RequestBody TrendAnalysisRequest request) {
        try {
            TrendAnalysisResponse response = trendService.analyzeTrends(
                    request.period(),
                    request.entity(),
                    request.start_date(),
                    request.end_date()
            );
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to analyze trends: " + e.getMessage(), 
                    e
            );
        }
    }
    
    /**
     * 특정 엔티티의 트렌드 조회
     * 
     * 특정 대상(연금펌드, 주제 등)에 대한 트렌드 데이터를 조회합니다.
     * 
     * @param entity 대상 엔티티 이름
     * @param period 분석 기간 (기본: weekly)
     * @param limit 조회할 최대 개수 (기본: 30)
     * @return List<TrendItem> 트렌드 데이터 목록
     */
    @GetMapping("/entity/{entity}")
    public ResponseEntity<List<TrendItem>> getEntityTrends(
            @PathVariable String entity,
            @RequestParam(defaultValue = "weekly") String period,
            @RequestParam(defaultValue = "30") int limit) {
        try {
            List<TrendItem> trends = trendService.getEntityTrends(
                    entity, 
                    period, 
                    limit
            );
            
            if (trends.isEmpty()) {
                throw new ResponseStatusException(
                        NOT_FOUND, 
                        "No trend data found for entity: " + entity
                );
            }
            
            return ResponseEntity.ok(trends);
        } catch (ResponseStatusException e) {
            throw e;
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to retrieve entity trends: " + e.getMessage(), 
                    e
            );
        }
    }
    
    /**
     * 인기 트렌드 조회
     * 
     * 현재 가장 인기 있는 트렌드를 조회합니다.
     * 볼륨과 감성 변화를 기준으로 정렬됩니다.
     * 
     * @param period 분석 기간 (기본: daily)
     * @param limit 조회할 최대 개수 (기본: 10)
     * @return List<PopularTrend> 인기 트렌드 목록
     */
    @GetMapping("/popular")
    public ResponseEntity<List<PopularTrend>> getPopularTrends(
            @RequestParam(defaultValue = "daily") String period,
            @RequestParam(defaultValue = "10") int limit) {
        try {
            List<PopularTrend> trends = trendService.getPopularTrends(
                    period, 
                    limit
            );
            return ResponseEntity.ok(trends);
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to retrieve popular trends: " + e.getMessage(), 
                    e
            );
        }
    }
    
    /**
     * 트렌딩 키워드 조회
     * 
     * 현재 트렌딩중인 주요 키워드를 추출합니다.
     * 빈도수와 중요도를 기준으로 순위가 매겨집니다.
     * 
     * @param period 분석 기간 (기본: daily)
     * @param limit 조회할 최대 개수 (기본: 20)
     * @return List<TrendingKeyword> 트렌딩 키워드 목록
     */
    @GetMapping("/keywords")
    public ResponseEntity<List<TrendingKeyword>> getTrendingKeywords(
            @RequestParam(defaultValue = "daily") String period,
            @RequestParam(defaultValue = "20") int limit) {
        try {
            List<TrendingKeyword> keywords = trendService.getTrendingKeywords(
                    period, 
                    limit
            );
            return ResponseEntity.ok(keywords);
        } catch (Exception e) {
            throw new ResponseStatusException(
                    INTERNAL_SERVER_ERROR, 
                    "Failed to retrieve trending keywords: " + e.getMessage(), 
                    e
            );
        }
    }
}
