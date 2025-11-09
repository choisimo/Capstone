package com.capstone.absa.repository;

import com.capstone.absa.entity.ABSAAnalysisEntity;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;

/**
 * ABSA 분석 결과 리포지토리
 * 
 * ABSA 분석 결과의 CRUD 작업을 위한 Spring Data JPA 리포지토리입니다.
 */
@Repository
public interface ABSAAnalysisRepository extends JpaRepository<ABSAAnalysisEntity, String> {

    /**
     * 컨텐츠 ID로 분석 결과 조회
     * 
     * @param contentId 컨텐츠 ID
     * @return 해당 컨텐츠의 분석 결과 리스트
     */
    List<ABSAAnalysisEntity> findByContentId(String contentId);

    /**
     * 컨텐츠 ID로 분석 결과 조회 (페이징)
     * 
     * @param contentId 컨텐츠 ID
     * @param pageable 페이징 정보
     * @return 페이징된 분석 결과
     */
    Page<ABSAAnalysisEntity> findByContentIdOrderByCreatedAtDesc(String contentId, Pageable pageable);

    /**
     * 컨텐츠 ID로 최신 분석 결과 조회
     * 
     * @param contentId 컨텐츠 ID
     * @return 최신 분석 결과
     */
    Optional<ABSAAnalysisEntity> findFirstByContentIdOrderByCreatedAtDesc(String contentId);

    /**
     * 특정 기간 내의 분석 결과 조회
     * 
     * @param startDate 시작 날짜
     * @param endDate 종료 날짜
     * @param pageable 페이징 정보
     * @return 페이징된 분석 결과
     */
    Page<ABSAAnalysisEntity> findByCreatedAtBetween(
        OffsetDateTime startDate, 
        OffsetDateTime endDate, 
        Pageable pageable
    );

    /**
     * 전체 감성 점수 범위로 분석 결과 조회
     * 
     * @param minScore 최소 점수
     * @param maxScore 최대 점수
     * @param pageable 페이징 정보
     * @return 페이징된 분석 결과
     */
    Page<ABSAAnalysisEntity> findByOverallSentimentBetween(
        Double minScore, 
        Double maxScore, 
        Pageable pageable
    );

    /**
     * 신뢰도 점수 이상의 분석 결과 조회
     * 
     * @param minConfidence 최소 신뢰도
     * @param pageable 페이징 정보
     * @return 페이징된 분석 결과
     */
    Page<ABSAAnalysisEntity> findByConfidenceScoreGreaterThanEqualOrderByCreatedAtDesc(
        Double minConfidence, 
        Pageable pageable
    );

    /**
     * 컨텐츠 ID 존재 여부 확인
     * 
     * @param contentId 컨텐츠 ID
     * @return 존재 여부
     */
    boolean existsByContentId(String contentId);

    /**
     * 특정 기간 내의 분석 결과 개수 조회
     * 
     * @param startDate 시작 날짜
     * @param endDate 종료 날짜
     * @return 분석 결과 개수
     */
    long countByCreatedAtBetween(OffsetDateTime startDate, OffsetDateTime endDate);
}
