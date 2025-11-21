package com.capstone.analysis.service;

import com.capstone.analysis.dto.TrainingDtos.CallbackRequest;
import com.capstone.analysis.dto.TrainingDtos.TaskType;
import com.capstone.analysis.dto.TrainingDtos.TrainRequest;
import com.capstone.analysis.dto.TrainingDtos.TrainingJobResponse;
import com.capstone.analysis.dto.TrainingDtos.TrainingStatus;
import com.capstone.analysis.entity.MLModelEntity;
import com.capstone.analysis.entity.TrainingJobEntity;
import com.capstone.analysis.infrastructure.ColabTrainingClient;
import com.capstone.analysis.repository.MLModelRepository;
import com.capstone.analysis.repository.TrainingJobRepository;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class TrainingService {

    private final TrainingJobRepository trainingJobRepository;
    private final MLModelRepository mlModelRepository;
    private final ColabTrainingClient colabTrainingClient;
    private final ObjectMapper objectMapper;

    @Transactional
    public TrainingJobResponse startTraining(TaskType taskType, Map<String, Object> dataset, Map<String, Object> hyperparameters, String datasetUrl, String callbackUrlBase) {
        String jobId = "train-" + UUID.randomUUID();

        TrainingJobEntity job = new TrainingJobEntity();
        job.setJobId(jobId);
        job.setTaskType(taskType.name());
        job.setStatus(TrainingStatus.PENDING.name());
        job.setCreatedAt(OffsetDateTime.now());
        job.setUpdatedAt(OffsetDateTime.now());
        trainingJobRepository.save(job);

        // Create a corresponding ML model record linked to this training job
        MLModelEntity model = new MLModelEntity();
        model.setName("Training_" + jobId);
        model.setVersion("train-" + jobId);
        model.setModelType(mapModelType(taskType));
        model.setFilePath(null);
        model.setIsActive(false);
        model.setHyperparameters(hyperparameters);
        model.setTrainingJobId(jobId);
        model.setTrainingStatus("pending");
        model.setTrainingProgress(0);
        mlModelRepository.save(model);

        String callbackUrl = callbackUrlBase + "/api/v1/training/callback";

        TrainRequest request = new TrainRequest(
                jobId,
                taskType,
                callbackUrl,
                hyperparameters,
                dataset,
                datasetUrl
        );

        colabTrainingClient.requestTraining(request);

        job.setStatus(TrainingStatus.QUEUED.name());
        trainingJobRepository.save(job);

        return new TrainingJobResponse(jobId, taskType, TrainingStatus.QUEUED, null, Map.of());
    }

    @Transactional
    public void handleCallback(CallbackRequest callbackRequest) {
        TrainingJobEntity job = trainingJobRepository.findById(callbackRequest.jobId())
                .orElseThrow(() -> new IllegalArgumentException("Training job not found: " + callbackRequest.jobId()));

        job.setStatus(callbackRequest.status());
        job.setModelPath(callbackRequest.modelPath());
        if (callbackRequest.metrics() != null) {
            job.setMetricsJson(writeJson(callbackRequest.metrics()));
        }
        job.setErrorMessage(callbackRequest.errorMessage());
        job.setUpdatedAt(OffsetDateTime.now());
        trainingJobRepository.save(job);

        // Update ML model entity associated with this training job
        mlModelRepository.findByTrainingJobId(job.getJobId()).ifPresent(model -> {
            model.setTrainingStatus(callbackRequest.status());
            if (callbackRequest.metrics() != null) {
                model.setMetrics(new java.util.HashMap<>(callbackRequest.metrics()));
            }
            model.setFilePath(callbackRequest.modelPath());
            if ("COMPLETED".equalsIgnoreCase(callbackRequest.status())) {
                model.setTrainingProgress(100);
                model.setTrainedAt(OffsetDateTime.now());
            }
            mlModelRepository.save(model);
        });
    }

    @Transactional(readOnly = true)
    public TrainingJobResponse getJob(String jobId) {
        TrainingJobEntity job = trainingJobRepository.findById(jobId)
                .orElseThrow(() -> new IllegalArgumentException("Training job not found: " + jobId));
        Map<String, Object> metrics = readJson(job.getMetricsJson());
        TaskType taskType = TaskType.valueOf(job.getTaskType());
        TrainingStatus status = TrainingStatus.valueOf(job.getStatus());
        return new TrainingJobResponse(job.getJobId(), taskType, status, job.getModelVersion(), metrics);
    }

    private String mapModelType(TaskType taskType) {
        if (taskType == TaskType.SENTIMENT) {
            return "sentiment";
        }
        if (taskType == TaskType.ABSA) {
            return "absa";
        }
        return taskType.name().toLowerCase();
    }

    private String writeJson(Object value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (Exception e) {
            throw new IllegalStateException(e);
        }
    }

    private Map<String, Object> readJson(String json) {
        if (json == null || json.isEmpty()) {
            return Map.of();
        }
        try {
            return objectMapper.readValue(json, new TypeReference<>() {});
        } catch (Exception e) {
            log.warn("Failed to parse metricsJson: {}", e.getMessage());
            return Map.of();
        }
    }
}
