package com.capstone.osint.planning.dto;

import jakarta.validation.constraints.NotBlank;
import java.util.List;
import java.util.UUID;

public final class PlanDtos {
    private PlanDtos() {}

    public record PlanCreateRequest(
            @NotBlank String name,
            List<String> goals,
            List<String> constraints
    ) {}

    public record PlanUpdateStatusRequest(
            @NotBlank String status
    ) {}

    public record PlanResponse(
            UUID id,
            String name,
            List<String> goals,
            List<String> constraints,
            String status
    ) {}
}
