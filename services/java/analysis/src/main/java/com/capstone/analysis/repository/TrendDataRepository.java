package com.capstone.analysis.repository;

import com.capstone.analysis.entity.TrendDataEntity;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.List;

@Repository
public interface TrendDataRepository extends JpaRepository<TrendDataEntity, Long> {
    
    /**
     * Find trend data for a specific entity and period within a date range
     */
    List<TrendDataEntity> findByEntityAndPeriodAndDateBetweenOrderByDateAsc(
            String entity, 
            String period, 
            OffsetDateTime startDate, 
            OffsetDateTime endDate
    );
    
    /**
     * Find all trends for an entity ordered by date
     */
    List<TrendDataEntity> findByEntityOrderByDateDesc(String entity, Pageable pageable);
    
    /**
     * Find popular trends (high volume) within a date range
     */
    @Query("SELECT t FROM TrendDataEntity t WHERE t.date BETWEEN :startDate AND :endDate " +
           "ORDER BY t.volume DESC")
    List<TrendDataEntity> findPopularTrends(
            @Param("startDate") OffsetDateTime startDate,
            @Param("endDate") OffsetDateTime endDate,
            Pageable pageable
    );
    
    /**
     * Find trends with specific direction
     */
    List<TrendDataEntity> findByTrendDirectionAndDateBetween(
            String trendDirection, 
            OffsetDateTime startDate, 
            OffsetDateTime endDate
    );
    
    /**
     * Calculate average sentiment for entity within date range
     */
    @Query("SELECT AVG(t.sentimentScore) FROM TrendDataEntity t " +
           "WHERE t.entity = :entity AND t.date BETWEEN :startDate AND :endDate")
    Double calculateAverageSentiment(
            @Param("entity") String entity,
            @Param("startDate") OffsetDateTime startDate,
            @Param("endDate") OffsetDateTime endDate
    );
    
    /**
     * Find latest trend data for each distinct entity
     */
    @Query("SELECT t FROM TrendDataEntity t WHERE t.date = " +
           "(SELECT MAX(t2.date) FROM TrendDataEntity t2 WHERE t2.entity = t.entity)")
    List<TrendDataEntity> findLatestTrendsPerEntity(Pageable pageable);
}
