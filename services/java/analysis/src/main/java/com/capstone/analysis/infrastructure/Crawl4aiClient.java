package com.capstone.analysis.infrastructure;

import com.capstone.analysis.dto.AgentDtos.AgentSource;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.util.Optional;

/**
 * Crawl4ai FastAPI 워커와 통신하는 최소 클라이언트.
 */
@Component
public class Crawl4aiClient {

    private final HttpClient httpClient;
    private final ObjectMapper mapper;
    private final String baseUrl;

    public Crawl4aiClient(
            ObjectMapper mapper,
            @Value("${analysis.crawl4ai.base-url:http://crawl4ai:8001}") String baseUrl
    ) {
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(5))
                .build();
        this.mapper = mapper;
        this.baseUrl = baseUrl;
    }

    /**
     * query가 URL로 보이는 경우에만 크롤 시도. 실패 시 Optional.empty().
     */
    public Optional<AgentSource> crawlIfUrl(String query) {
        String trimmed = query == null ? "" : query.trim();
        if (!(trimmed.startsWith("http://") || trimmed.startsWith("https://"))) {
            return Optional.empty();
        }

        try {
            String body = mapper.createObjectNode()
                    .put("url", trimmed)
                    .put("js_render", false)
                    .toString();

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(baseUrl + "/crawl"))
                    .timeout(Duration.ofSeconds(30))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(body))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() / 100 != 2) {
                return Optional.empty();
            }

            JsonNode json = mapper.readTree(response.body());
            String status = json.path("status").asText("");
            if (!"SUCCESS".equalsIgnoreCase(status)) {
                return Optional.empty();
            }

            String url = json.path("url").asText(trimmed);
            String markdown = json.path("markdown").asText("");
            if (markdown.isEmpty()) {
                return Optional.empty();
            }

            String snippet = markdown.length() > 500 ? markdown.substring(0, 500) + "..." : markdown;
            return Optional.of(new AgentSource(url, url, snippet));
        } catch (IOException | InterruptedException e) {
            Thread.currentThread().interrupt();
            return Optional.empty();
        }
    }
}
