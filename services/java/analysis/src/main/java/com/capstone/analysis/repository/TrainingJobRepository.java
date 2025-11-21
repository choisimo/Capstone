package com.capstone.analysis.repository;

import com.capstone.analysis.entity.TrainingJobEntity;
import org.springframework.data.jpa.repository.JpaRepository;

public interface TrainingJobRepository extends JpaRepository<TrainingJobEntity, String> {
}
