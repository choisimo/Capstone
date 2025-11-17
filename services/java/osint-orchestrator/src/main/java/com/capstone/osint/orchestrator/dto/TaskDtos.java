package com.capstone.osint.orchestrator.dto;

import jakarta.validation.constraints.NotBlank;
import java.util.List;
import java.util.UUID;

public final class TaskDtos {
    private TaskDtos() {}

    public record TaskCreateRequest(
            @NotBlank String name,
            List<String> sourceIds,
            List<String> filterPipeline
    ) {}

    public record TaskResponse(
            UUID id,
            String name,
            List<String> sourceIds,
            List<String> filterPipeline,
            String status
    ) {}
}
