package com.capstone.osint.orchestrator.service;

import com.capstone.osint.orchestrator.dto.TaskDtos.TaskCreateRequest;
import com.capstone.osint.orchestrator.dto.TaskDtos.TaskResponse;
import jakarta.validation.Valid;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class TaskService {

    private static class TaskModel {
        UUID id;
        String name;
        List<String> sourceIds;
        List<String> filterPipeline;
        String status;
    }

    private final Map<UUID, TaskModel> store = new ConcurrentHashMap<>();

    public TaskResponse create(@Valid TaskCreateRequest req) {
        TaskModel m = new TaskModel();
        m.id = UUID.randomUUID();
        m.name = req.name();
        m.sourceIds = req.sourceIds() != null ? new ArrayList<>(req.sourceIds()) : List.of();
        m.filterPipeline = req.filterPipeline() != null ? new ArrayList<>(req.filterPipeline()) : List.of();
        m.status = "CREATED";
        store.put(m.id, m);
        return toDto(m);
    }

    public List<TaskResponse> list() {
        return store.values().stream().map(this::toDto).collect(java.util.stream.Collectors.toList());
    }

    public TaskResponse run(UUID id) {
        TaskModel m = store.get(id);
        if (m == null) throw new IllegalArgumentException("Task not found: " + id);
        m.status = "RUNNING";
        return toDto(m);
    }

    public TaskResponse get(UUID id) {
        TaskModel m = store.get(id);
        if (m == null) throw new IllegalArgumentException("Task not found: " + id);
        return toDto(m);
    }

    private TaskResponse toDto(TaskModel m) {
        return new TaskResponse(m.id, m.name, m.sourceIds, m.filterPipeline, m.status);
        
    }
}
