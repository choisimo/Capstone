package com.capstone.absa.repository;

import com.capstone.absa.entity.AspectModelEntity;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * 속성 모델 리포지토리
 * 
 * 속성 모델의 CRUD 작업을 위한 Spring Data JPA 리포지토리입니다.
 */
@Repository
public interface AspectModelRepository extends JpaRepository<AspectModelEntity, String> {

    /**
     * 이름으로 속성 모델 조회
     * 
     * @param name 속성 이름
     * @return 속성 모델
     */
    Optional<AspectModelEntity> findByName(String name);

    /**
     * 활성화 상태로 속성 모델 조회
     * 
     * @param isActive 활성화 상태 (1: 활성, 0: 비활성)
     * @return 활성화된 속성 모델 리스트
     */
    List<AspectModelEntity> findByIsActive(Integer isActive);

    /**
     * 활성화 상태로 속성 모델 조회 (페이징)
     * 
     * @param isActive 활성화 상태
     * @param pageable 페이징 정보
     * @return 페이징된 속성 모델
     */
    Page<AspectModelEntity> findByIsActive(Integer isActive, Pageable pageable);

    /**
     * 모델 버전으로 속성 모델 조회
     * 
     * @param modelVersion 모델 버전
     * @return 해당 버전의 속성 모델 리스트
     */
    List<AspectModelEntity> findByModelVersion(String modelVersion);

    /**
     * 이름 존재 여부 확인
     * 
     * @param name 속성 이름
     * @return 존재 여부
     */
    boolean existsByName(String name);

    /**
     * 활성화된 속성 모델 개수 조회
     * 
     * @return 활성화된 속성 모델 개수
     */
    @Query("SELECT COUNT(a) FROM AspectModelEntity a WHERE a.isActive = 1")
    long countActiveModels();

    /**
     * 이름으로 검색 (부분 일치, 대소문자 무시)
     * 
     * @param name 검색할 이름
     * @param pageable 페이징 정보
     * @return 페이징된 속성 모델
     */
    Page<AspectModelEntity> findByNameContainingIgnoreCase(String name, Pageable pageable);

    /**
     * 활성화 상태와 모델 버전으로 속성 모델 조회
     * 
     * @param isActive 활성화 상태
     * @param modelVersion 모델 버전
     * @return 해당 조건의 속성 모델 리스트
     */
    List<AspectModelEntity> findByIsActiveAndModelVersion(Integer isActive, String modelVersion);
}
