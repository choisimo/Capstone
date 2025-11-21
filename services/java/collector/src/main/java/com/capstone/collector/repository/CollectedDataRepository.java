package com.capstone.collector.repository;

import com.capstone.collector.entity.CollectedDataEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface CollectedDataRepository extends JpaRepository<CollectedDataEntity, UUID> {
    List<CollectedDataEntity> findBySourceId(UUID sourceId);
    List<CollectedDataEntity> findByProcessed(Boolean processed);
    List<CollectedDataEntity> findBySourceIdAndProcessed(UUID sourceId, Boolean processed);
}
