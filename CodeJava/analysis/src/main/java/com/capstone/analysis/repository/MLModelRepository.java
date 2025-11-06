package com.capstone.analysis.repository;

import com.capstone.analysis.entity.MLModelEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface MLModelRepository extends JpaRepository<MLModelEntity, Long> {
    
    /**
     * Find all models by type
     */
    List<MLModelEntity> findByModelTypeOrderByCreatedAtDesc(String modelType);
    
    /**
     * Find active models by type
     */
    List<MLModelEntity> findByModelTypeAndIsActiveTrueOrderByCreatedAtDesc(String modelType);
    
    /**
     * Find the currently active model of a given type
     */
    Optional<MLModelEntity> findFirstByModelTypeAndIsActiveTrueOrderByCreatedAtDesc(String modelType);
    
    /**
     * Find model by name and version
     */
    Optional<MLModelEntity> findByNameAndVersion(String name, String version);
    
    /**
     * Find all active models
     */
    List<MLModelEntity> findByIsActiveTrueOrderByCreatedAtDesc();
    
    /**
     * Find model by training job ID
     */
    Optional<MLModelEntity> findByTrainingJobId(String trainingJobId);
    
    /**
     * Deactivate all models of a specific type
     */
    @Modifying
    @Query("UPDATE MLModelEntity m SET m.isActive = false WHERE m.modelType = :modelType AND m.isActive = true")
    int deactivateAllByModelType(@Param("modelType") String modelType);
    
    /**
     * Count active models
     */
    long countByIsActiveTrue();
    
    /**
     * Find models by training status
     */
    List<MLModelEntity> findByTrainingStatusOrderByCreatedAtDesc(String trainingStatus);
}
