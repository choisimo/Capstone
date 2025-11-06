package com.capstone.collector.repository;

import com.capstone.collector.entity.CollectedDataEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CollectedDataRepository extends JpaRepository<CollectedDataEntity, Long> {
    List<CollectedDataEntity> findBySourceId(Long sourceId);
    List<CollectedDataEntity> findByProcessed(Boolean processed);
    List<CollectedDataEntity> findBySourceIdAndProcessed(Long sourceId, Boolean processed);
}
