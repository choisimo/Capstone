package com.capstone.analysis.infrastructure;

import com.capstone.analysis.dto.AgentDtos.AgentSource;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

/**
 * Perplexity AI HTTP client.
 *
 * API 키는 Consul KV에서 동적으로 조회합니다.
 * - 기본 경로: config/analysis/dev/secrets/perplexity/api_key
 */
@Component
public class PerplexityClient {

    private final ConsulKvClient consulKvClient;
    private final HttpClient httpClient;
    private final ObjectMapper mapper;
    private final String kvKeyPath;
    private final String apiBaseUrl;
    private final String model;

    public PerplexityClient(
            ConsulKvClient consulKvClient,
            ObjectMapper mapper,
            @Value("${analysis.perplexity.kv-key:config/analysis/dev/secrets/perplexity/api_key}") String kvKeyPath,
            @Value("${analysis.perplexity.base-url:https://api.perplexity.ai}") String apiBaseUrl,
            @Value("${analysis.perplexity.model:llama-3-sonar-small-32k-online}") String model
    ) {
        this.consulKvClient = consulKvClient;
        this.mapper = mapper;
        this.kvKeyPath = kvKeyPath;
        this.apiBaseUrl = apiBaseUrl;
        this.model = model;
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(5))
                .build();
    }

    public PerplexityResult query(String query) {
        String apiKey = consulKvClient.getRawValue(kvKeyPath)
                .orElseThrow(() -> new IllegalStateException("Perplexity API key not found in Consul at " + kvKeyPath));

        try {
            String body = buildRequestBody(query);

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(apiBaseUrl + "/chat/completions"))
                    .timeout(Duration.ofSeconds(30))
                    .header("Authorization", "Bearer " + apiKey)
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() / 100 != 2) {
                throw new IllegalStateException(
                    "Perplexity API error: status=" + response.statusCode() + 
                    ", body=" + response.body());
            }

            return parseResponse(query, response.body());
        } catch (IOException | InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Perplexity API call failed", e);
        }
    }

    private String buildRequestBody(String query) throws IOException {
        ObjectNode root = mapper.createObjectNode();
        root.put("model", model);
        ArrayNode messages = root.putArray("messages");

        ObjectNode system = messages.addObject();
        system.put("role", "system");
        system.put("content", "You are an analysis assistant for pension sentiment and OSINT data. Provide concise Korean summaries and key points.");

        ObjectNode user = messages.addObject();
        user.put("role", "user");
        user.put("content", query);

        root.put("temperature", 0.2);

        return mapper.writeValueAsString(root);
    }

    private PerplexityResult parseResponse(String query, String body) throws IOException {
        JsonNode json = mapper.readTree(body);
        String answer = json.path("choices").path(0).path("message").path("content").asText("");

        // Perplexity 응답에서 참조 URL이 제공되는 경우 sources로 매핑
        List<AgentSource> sources = new ArrayList<>();
        JsonNode references = json.path("references");
        if (references.isArray()) {
            for (JsonNode ref : references) {
                String url = ref.path("url").asText("");
                if (!url.isEmpty()) {
                    String title = ref.path("title").asText(url);
                    String snippet = ref.path("snippet").asText("");
                    sources.add(new AgentSource(title, url, snippet));
                }
            }
        }

        // confidence는 현재 Perplexity에서 별도 점수를 제공하지 않으므로 고정값 사용
        double confidence = answer.isEmpty() ? 0.0 : 1.0;
        return new PerplexityResult(answer, confidence, sources);
    }

    public record PerplexityResult(String answer, double confidence, List<AgentSource> sources) {}
}
