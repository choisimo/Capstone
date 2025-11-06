package com.capstone.analysis.repository;

import com.capstone.analysis.entity.SentimentAnalysisEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.List;

@Repository
public interface SentimentAnalysisRepository extends JpaRepository<SentimentAnalysisEntity, Long> {
    
    /**
     * Find all sentiment analyses for a given content ID
     */
    List<SentimentAnalysisEntity> findByContentIdOrderByAnalyzedAtDesc(String contentId);
    
    /**
     * Find sentiment analyses within a date range
     */
    List<SentimentAnalysisEntity> findByAnalyzedAtBetween(OffsetDateTime startDate, OffsetDateTime endDate);
    
    /**
     * Count analyses by sentiment label within a date range
     */
    @Query("SELECT COUNT(s) FROM SentimentAnalysisEntity s WHERE s.sentimentLabel = :label " +
           "AND s.analyzedAt BETWEEN :startDate AND :endDate")
    long countBySentimentLabelAndDateRange(
            @Param("label") String label,
            @Param("startDate") OffsetDateTime startDate,
            @Param("endDate") OffsetDateTime endDate
    );
    
    /**
     * Calculate average sentiment score within a date range
     */
    @Query("SELECT AVG(s.sentimentScore) FROM SentimentAnalysisEntity s " +
           "WHERE s.analyzedAt BETWEEN :startDate AND :endDate")
    Double calculateAverageSentimentScore(
            @Param("startDate") OffsetDateTime startDate,
            @Param("endDate") OffsetDateTime endDate
    );
    
    /**
     * Calculate average confidence within a date range
     */
    @Query("SELECT AVG(s.confidence) FROM SentimentAnalysisEntity s " +
           "WHERE s.analyzedAt BETWEEN :startDate AND :endDate")
    Double calculateAverageConfidence(
            @Param("startDate") OffsetDateTime startDate,
            @Param("endDate") OffsetDateTime endDate
    );
}
