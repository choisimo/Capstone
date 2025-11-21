package com.capstone.collector.repository;

import com.capstone.collector.entity.CollectionJobEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface CollectionJobRepository extends JpaRepository<CollectionJobEntity, UUID> {
    List<CollectionJobEntity> findBySourceId(UUID sourceId);
    List<CollectionJobEntity> findByStatus(String status);
}
