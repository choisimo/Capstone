package com.capstone.analysis.service;

import com.capstone.analysis.dto.TrendDtos.*;
import com.capstone.analysis.entity.TrendDataEntity;
import com.capstone.analysis.repository.TrendDataRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 트렌드 분석 서비스
 * 
 * 시간에 따른 감성 및 볼륨 트렌드를 분석하는 비즈니스 로직을 담당합니다.
 */
@Service
public class TrendService {
    
    private final TrendDataRepository trendDataRepository;
    
    public TrendService(TrendDataRepository trendDataRepository) {
        this.trendDataRepository = trendDataRepository;
    }
    
    /**
     * 트렌드 분석 수행
     * 
     * @param period 분석 기간 (daily/weekly/monthly)
     * @param entity 분석 대상 엔티티
     * @param startDate 시작 날짜
     * @param endDate 종료 날짜
     * @return TrendAnalysisResponse 트렌드 분석 결과
     */
    public TrendAnalysisResponse analyzeTrends(
            String period, 
            String entity, 
            OffsetDateTime startDate, 
            OffsetDateTime endDate) {
        // Query trend data from database
        LocalDate start = startDate.toLocalDate();
        LocalDate end = endDate.toLocalDate();
        
        List<TrendDataEntity> trendEntities = trendDataRepository
                .findByEntityAndPeriodAndDateBetweenOrderByDateAsc(entity, period, start, end);
        
        // Convert to TrendItem DTOs
        List<TrendItem> dataPoints = trendEntities.stream()
                .map(e -> new TrendItem(
                        e.getDate().atStartOfDay().atOffset(OffsetDateTime.now().getOffset()),
                        e.getSentimentScore(),
                        e.getVolume(),
                        e.getKeywords() != null ? List.of(e.getKeywords()) : List.of()
                ))
                .collect(Collectors.toList());
        
        // Calculate trend direction and strength
        String trendDirection = calculateTrendDirection(trendEntities);
        double trendStrength = calculateTrendStrength(trendEntities);
        
        return new TrendAnalysisResponse(
                period,
                entity,
                trendDirection,
                trendStrength,
                dataPoints,
                String.format("Trend analysis for %s over %s period with %d data points", 
                        entity, period, dataPoints.size())
        );
    }
    
    private String calculateTrendDirection(List<TrendDataEntity> trends) {
        if (trends.size() < 2) {
            return "stable";
        }
        
        // Simple linear trend calculation
        double firstHalfAvg = trends.subList(0, trends.size() / 2).stream()
                .mapToDouble(TrendDataEntity::getSentimentScore)
                .average()
                .orElse(0.0);
        
        double secondHalfAvg = trends.subList(trends.size() / 2, trends.size()).stream()
                .mapToDouble(TrendDataEntity::getSentimentScore)
                .average()
                .orElse(0.0);
        
        double diff = secondHalfAvg - firstHalfAvg;
        if (Math.abs(diff) < 0.1) {
            return "stable";
        }
        return diff > 0 ? "increasing" : "decreasing";
    }
    
    private double calculateTrendStrength(List<TrendDataEntity> trends) {
        if (trends.isEmpty()) {
            return 0.0;
        }
        
        // Calculate coefficient of variation
        double mean = trends.stream()
                .mapToDouble(TrendDataEntity::getSentimentScore)
                .average()
                .orElse(0.0);
        
        double variance = trends.stream()
                .mapToDouble(t -> Math.pow(t.getSentimentScore() - mean, 2))
                .average()
                .orElse(0.0);
        
        double stdDev = Math.sqrt(variance);
        return mean != 0 ? Math.abs(stdDev / mean) : 0.0;
    }
    
    /**
     * 특정 엔티티의 트렌드 조회
     * 
     * @param entity 엔티티 이름
     * @param period 분석 기간
     * @param limit 조회 개수
     * @return List<TrendItem> 트렌드 데이터 목록
     */
    public List<TrendItem> getEntityTrends(String entity, String period, int limit) {
        // Query latest trends for entity
        List<TrendDataEntity> trendEntities = trendDataRepository
                .findLatestTrendsPerEntity(entity, period, PageRequest.of(0, limit));
        
        return trendEntities.stream()
                .map(e -> new TrendItem(
                        e.getDate().atStartOfDay().atOffset(OffsetDateTime.now().getOffset()),
                        e.getSentimentScore(),
                        e.getVolume(),
                        e.getKeywords() != null ? List.of(e.getKeywords()) : List.of()
                ))
                .collect(Collectors.toList());
    }
    
    /**
     * 인기 트렌드 조회
     * 
     * @param period 분석 기간
     * @param limit 조회 개수
     * @return List<PopularTrend> 인기 트렌드 목록
     */
    public List<PopularTrend> getPopularTrends(String period, int limit) {
        // Query popular trends by volume
        List<TrendDataEntity> popularEntities = trendDataRepository
                .findPopularTrends(period, PageRequest.of(0, limit));
        
        return popularEntities.stream()
                .map(e -> new PopularTrend(
                        e.getEntity(),
                        e.getVolume(),
                        e.getSentimentScore(),
                        e.getTrendDirection(),
                        e.getKeywords() != null ? List.of(e.getKeywords()) : List.of()
                ))
                .collect(Collectors.toList());
    }
    
    /**
     * 트렌딩 키워드 조회
     * 
     * @param period 분석 기간
     * @param limit 조회 개수
     * @return List<TrendingKeyword> 트렌딩 키워드 목록
     */
    public List<TrendingKeyword> getTrendingKeywords(String period, int limit) {
        // Query trends and extract keywords
        List<TrendDataEntity> trends = trendDataRepository
                .findPopularTrends(period, PageRequest.of(0, limit * 3));
        
        // Aggregate keywords across trends
        List<TrendingKeyword> keywords = new ArrayList<>();
        
        for (TrendDataEntity trend : trends) {
            if (trend.getKeywords() != null) {
                for (String keyword : trend.getKeywords()) {
                    // Calculate aggregated metrics for each keyword
                    String sentimentLabel = trend.getSentimentScore() > 0.3 ? "positive" 
                            : trend.getSentimentScore() < -0.3 ? "negative" : "neutral";
                    
                    keywords.add(new TrendingKeyword(
                            keyword,
                            trend.getVolume(),
                            Math.abs(trend.getTrendStrength()),
                            sentimentLabel
                    ));
                }
            }
            
            if (keywords.size() >= limit) {
                break;
            }
        }
        
        return keywords.stream()
                .limit(limit)
                .collect(Collectors.toList());
    }
}
