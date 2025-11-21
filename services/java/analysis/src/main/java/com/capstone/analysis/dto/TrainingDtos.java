package com.capstone.analysis.dto;

import java.util.Map;

/**
 * DTO definitions for managing ML training jobs executed via Colab.
 */
public class TrainingDtos {

    public enum TaskType { SENTIMENT, ABSA }

    public enum TrainingStatus { PENDING, QUEUED, RUNNING, COMPLETED, FAILED, CANCELED }

    public record TrainRequest(
            String jobId,
            TaskType taskType,
            String callbackUrl,
            Map<String, Object> hyperparameters,
            Map<String, Object> dataset,
            String datasetUrl
    ) {}

    public record CallbackRequest(
            String jobId,
            String status,
            Map<String, Double> metrics,
            String modelPath,
            String errorMessage
    ) {}

    public record TrainingJobResponse(
            String jobId,
            TaskType taskType,
            TrainingStatus status,
            String modelVersion,
            Map<String, Object> lastMetrics
    ) {}
}
