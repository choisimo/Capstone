package com.capstone.collector.repository;

import com.capstone.collector.entity.CollectionJobEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface CollectionJobRepository extends JpaRepository<CollectionJobEntity, Long> {
    List<CollectionJobEntity> findBySourceId(Long sourceId);
    List<CollectionJobEntity> findByStatus(String status);
}
