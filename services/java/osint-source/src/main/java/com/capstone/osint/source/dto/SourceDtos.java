package com.capstone.osint.source.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import java.util.List;
import java.util.UUID;

public final class SourceDtos {
    private SourceDtos() {}

    public record SourceCreateRequest(
            @NotBlank String name,
            @NotBlank @Pattern(regexp = "https?://.+") String url,
            List<String> tags,
            Boolean active
    ) {}

    public record SourceUpdateRequest(
            String name,
            String url,
            List<String> tags,
            Boolean active
    ) {}

    public record SourceResponse(
            UUID id,
            String name,
            String url,
            List<String> tags,
            boolean active
    ) {}
}
