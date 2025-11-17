package com.capstone.osint.orchestrator.controller;

import com.capstone.osint.orchestrator.dto.TaskDtos.TaskCreateRequest;
import com.capstone.osint.orchestrator.dto.TaskDtos.TaskResponse;
import com.capstone.osint.orchestrator.service.TaskService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/osint-orchestrator/tasks")
public class TaskController {

    private final TaskService taskService;

    public TaskController(TaskService taskService) {
        this.taskService = taskService;
    }

    @PostMapping
    public ResponseEntity<TaskResponse> create(@RequestBody @Valid TaskCreateRequest req) {
        TaskResponse created = taskService.create(req);
        return ResponseEntity.created(URI.create("/api/v1/osint-orchestrator/tasks/" + created.id()))
                .body(created);
    }

    @GetMapping
    public ResponseEntity<List<TaskResponse>> list() {
        return ResponseEntity.ok(taskService.list());
    }

    @PostMapping("/{id}/run")
    public ResponseEntity<TaskResponse> run(@PathVariable UUID id) {
        return ResponseEntity.ok(taskService.run(id));
    }

    @GetMapping("/{id}")
    public ResponseEntity<TaskResponse> get(@PathVariable UUID id) {
        return ResponseEntity.ok(taskService.get(id));
    }
}
