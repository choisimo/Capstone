package com.capstone.osint.source.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;

@Service
public class PerplexityService {

    private final ObjectMapper mapper = new ObjectMapper();

    @Value("${perplexity.api.url:https://api.perplexity.ai/chat/completions}")
    private String apiUrl;

    @Value("${perplexity.api.key:}")
    private String apiKey;

    @Value("${perplexity.model:sonar}")
    private String model;

    public String enrich(String content, String query) {
        if (!StringUtils.hasText(apiKey)) return content;
        try {
            String prompt = buildPrompt(content, query);
            String body = mapper.createObjectNode()
                    .put("model", model)
                    .set("messages", mapper.createArrayNode()
                            .add(mapper.createObjectNode()
                                    .put("role", "user")
                                    .put("content", prompt)))
                    .toString();
            HttpClient client = HttpClient.newHttpClient();
            HttpRequest req = HttpRequest.newBuilder(URI.create(apiUrl))
                    .header("Content-Type", "application/json")
                    .header("Authorization", "Bearer " + apiKey)
                    .POST(HttpRequest.BodyPublishers.ofString(body, StandardCharsets.UTF_8))
                    .build();
            HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            String payload = resp.body();
            JsonNode json = mapper.readTree(payload);
            JsonNode choices = json.get("choices");
            if (choices != null && choices.isArray() && choices.size() > 0) {
                JsonNode msg = choices.get(0).get("message");
                if (msg != null && msg.has("content")) {
                    return content + "\n\n[perplexity] " + msg.get("content").asText();
                }
            }
        } catch (Exception ignored) {}
        return content;
    }

    private String buildPrompt(String content, String query) {
        StringBuilder sb = new StringBuilder();
        sb.append("Given the crawled web content below, extract key facts, entities, and signals. If a user query is provided, focus on aspects relevant to it. Return concise bullet points without omitting important details.\n\n");
        if (StringUtils.hasText(query)) {
            sb.append("User Query: ").append(query).append("\n\n");
        }
        sb.append("Content:\n").append(content);
        return sb.toString();
    }
}
