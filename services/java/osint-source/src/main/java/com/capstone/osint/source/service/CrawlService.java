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
public class CrawlService {

    private final ObjectMapper mapper = new ObjectMapper();

    @Value("${crawl4ai.url:}")
    private String crawl4aiUrl;

    @Value("${crawl4ai.endpoint:/api/crawl}")
    private String crawl4aiEndpoint;

    public String fetch(String url) {
        if (StringUtils.hasText(crawl4aiUrl)) {
            try {
                return fetchViaCrawl4ai(url);
            } catch (Exception ignored) {
            }
        }
        return fetchViaHttp(url);
    }

    private String fetchViaHttp(String url) {
        try {
            HttpClient client = HttpClient.newHttpClient();
            HttpRequest req = HttpRequest.newBuilder(URI.create(url)).GET().build();
            HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            return resp.body();
        } catch (Exception e) {
            throw new IllegalArgumentException("Fetch failed: " + e.getMessage());
        }
    }

    private String fetchViaCrawl4ai(String url) throws Exception {
        String endpoint = crawl4aiUrl + (crawl4aiEndpoint.startsWith("/") ? crawl4aiEndpoint : "/" + crawl4aiEndpoint);
        HttpClient client = HttpClient.newHttpClient();
        String body = mapper.createObjectNode().put("url", url).toString();
        HttpRequest req = HttpRequest.newBuilder(URI.create(endpoint))
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(body, StandardCharsets.UTF_8))
                .build();
        HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
        String payload = resp.body();
        JsonNode json = mapper.readTree(payload);
        if (json.has("content")) return json.get("content").asText();
        if (json.has("text")) return json.get("text").asText();
        return payload;
    }
}
