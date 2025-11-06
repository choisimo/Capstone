package com.capstone.analysis.repository;

import com.capstone.analysis.entity.ReportEntity;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface ReportRepository extends JpaRepository<ReportEntity, Long> {
    
    /**
     * Find reports by type
     */
    List<ReportEntity> findByReportTypeOrderByCreatedAtDesc(String reportType, Pageable pageable);
    
    /**
     * Find reports by status
     */
    List<ReportEntity> findByStatusOrderByCreatedAtDesc(String status, Pageable pageable);
    
    /**
     * Find all reports ordered by creation date
     */
    List<ReportEntity> findAllByOrderByCreatedAtDesc(Pageable pageable);
    
    /**
     * Find reports created within a date range
     */
    List<ReportEntity> findByCreatedAtBetweenOrderByCreatedAtDesc(
            OffsetDateTime startDate, 
            OffsetDateTime endDate
    );
    
    /**
     * Count reports by status
     */
    long countByStatus(String status);
    
    /**
     * Find reports by title containing search term
     */
    List<ReportEntity> findByTitleContainingIgnoreCaseOrderByCreatedAtDesc(
            String searchTerm, 
            Pageable pageable
    );
    
    /**
     * Find report by ID and status
     */
    Optional<ReportEntity> findByIdAndStatus(Long id, String status);
}
