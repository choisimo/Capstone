package com.capstone.analysis.dto;

import java.time.Instant;
import java.util.List;

public class AgentDtos {

    public record AgentSearchRequest(String query) {}

    public record AgentSource(String title, String url, String snippet) {}

    public record AgentSearchResponse(
            String id,
            String query,
            String response,
            List<AgentSource> sources,
            double confidence,
            Instant timestamp
    ) {}

    public record AiChatRequest(
            String message,
            String title,
            String providerId,
            String modelId
    ) {}

    public record AiChatResponse(
            String sessionId,
            String reply,
            Object rawResponse
    ) {}
}
