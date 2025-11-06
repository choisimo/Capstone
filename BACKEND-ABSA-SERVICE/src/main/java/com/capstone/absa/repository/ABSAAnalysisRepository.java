package com.capstone.absa.repository;

import com.capstone.absa.model.ABSAAnalysis;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ABSAAnalysisRepository extends JpaRepository<ABSAAnalysis, Long> {
    
    List<ABSAAnalysis> findByContentIdOrderByCreatedAtDesc(String contentId);
}
