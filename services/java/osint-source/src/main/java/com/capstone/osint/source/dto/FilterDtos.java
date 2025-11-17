package com.capstone.osint.source.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.util.List;
import java.util.Map;

public final class FilterDtos {
    private FilterDtos() {}

    public record FilterStep(
            @NotBlank String filterId,
            @NotNull Map<String, Object> config
    ) {}

    public record ApplyRequest(
            @NotBlank String content,
            List<FilterStep> steps
    ) {}

    public record ApplyResponse(
            String originalContent,
            String finalContent
    ) {}

    public record CrawlAndFilterRequest(
            @NotBlank String url,
            List<FilterStep> steps,
            Boolean usePerplexity,
            String perplexityQuery
    ) {}

    public record CrawlAndFilterResponse(
            String url,
            String crawledContent,
            String finalContent
    ) {}
}
