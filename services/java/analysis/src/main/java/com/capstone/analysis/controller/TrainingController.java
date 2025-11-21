package com.capstone.analysis.controller;

import com.capstone.analysis.dto.TrainingDtos.CallbackRequest;
import com.capstone.analysis.dto.TrainingDtos.TaskType;
import com.capstone.analysis.dto.TrainingDtos.TrainingJobResponse;
import com.capstone.analysis.service.TrainingService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/training")
@RequiredArgsConstructor
public class TrainingController {

    private final TrainingService trainingService;

    @PostMapping("/{taskType}/start")
    public ResponseEntity<TrainingJobResponse> start(
            @PathVariable String taskType,
            @RequestBody Map<String, Object> body,
            @RequestHeader(name = "X-Callback-Base", required = false) String callbackBase
    ) {
        TaskType type = TaskType.valueOf(taskType.toUpperCase());
        @SuppressWarnings("unchecked")
        Map<String, Object> dataset = (Map<String, Object>) body.getOrDefault("dataset", Map.of());
        @SuppressWarnings("unchecked")
        Map<String, Object> hyperparameters = (Map<String, Object>) body.getOrDefault("hyperparameters", Map.of());
        String datasetUrl = body.get("datasetUrl") instanceof String s ? s : null;
        String callbackBaseUrl = callbackBase != null ? callbackBase : "http://localhost:8080";

        TrainingJobResponse response = trainingService.startTraining(type, dataset, hyperparameters, datasetUrl, callbackBaseUrl);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/{jobId}")
    public ResponseEntity<TrainingJobResponse> get(@PathVariable String jobId) {
        return ResponseEntity.ok(trainingService.getJob(jobId));
    }

    @PostMapping("/callback")
    public ResponseEntity<Void> callback(@RequestBody CallbackRequest callbackRequest) {
        trainingService.handleCallback(callbackRequest);
        return ResponseEntity.ok().build();
    }
}
