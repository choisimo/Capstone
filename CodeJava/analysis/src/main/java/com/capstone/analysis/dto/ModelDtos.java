package com.capstone.analysis.dto;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

public class ModelDtos {
    
    public record MLModelRequest(
            String name,
            String model_type,
            String file_path,
            Map<String, Object> metrics
    ) {}
    
    public record MLModelResponse(
            Long model_id,
            String name,
            String version,
            String model_type,
            boolean is_active,
            Map<String, Object> metrics,
            OffsetDateTime created_at
    ) {}
    
    public record ModelTrainingRequest(
            String model_name,
            String training_data_path,
            Map<String, Object> hyperparameters,
            double validation_split
    ) {}
    
    public record ModelTrainingResponse(
            String job_id,
            String status,
            OffsetDateTime estimated_completion
    ) {}
    
    public record TrainingStatus(
            String job_id,
            String status,
            int progress,
            Map<String, Object> metrics,
            OffsetDateTime started_at,
            OffsetDateTime updated_at
    ) {}
}
