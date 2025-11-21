package com.capstone.analysis.infrastructure;

import com.capstone.analysis.dto.AgentDtos.AgentSource;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

/**
 * Client for changedetection.io API.
 *
 * - API key is read from Consul KV to avoid hardcoding secrets.
 * - Watches are searched by URL/title (and optional tag), then latest snapshots
 *   are fetched and mapped to AgentSource entries.
 */
@Component
public class ChangeDetectionClient {

    private static final Logger log = LoggerFactory.getLogger(ChangeDetectionClient.class);

    private final ConsulKvClient consulKvClient;
    private final HttpClient httpClient;
    private final ObjectMapper mapper;
    private final String kvKeyPath;
    private final String baseUrl;
    private final String defaultTag;

    public ChangeDetectionClient(
            ConsulKvClient consulKvClient,
            ObjectMapper mapper,
            @Value("${analysis.changedetection.kv-key:config/analysis/dev/secrets/changedetection/api_key}") String kvKeyPath,
            @Value("${analysis.changedetection.base-url:${CHANGEDETECTION_BASE_URL:http://changedetection:5000}}") String baseUrl,
            @Value("${analysis.changedetection.search-tag:${CHANGEDETECTION_SEARCH_TAG:}}") String defaultTag
    ) {
        this.consulKvClient = consulKvClient;
        this.mapper = mapper;
        this.kvKeyPath = kvKeyPath;
        this.baseUrl = baseUrl;
        this.defaultTag = defaultTag;
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(5))
                .build();
    }

    /**
     * Search watches in changedetection.io and return latest snapshots as AgentSource list.
     *
     * - If API key is missing or any error occurs, returns an empty list.
     * - Optionally filters by tag (configured via analysis.changedetection.search-tag or CHANGEDETECTION_SEARCH_TAG).
     */
    public List<AgentSource> searchLatestChanges(String query) {
        log.info("searchLatestChanges called with query: {}", query);
        
        String apiKey = consulKvClient.getRawValue(kvKeyPath).orElse(null);
        if (apiKey == null || apiKey.isBlank()) {
            log.warn("API key is null or blank from KV path: {}", kvKeyPath);
            return Collections.emptyList();
        }
        log.info("API key retrieved successfully, length: {}", apiKey.length());

        try {
            List<WatchInfo> watches = searchWatches(apiKey, query);
            log.info("Found {} watches matching query", watches.size());
            
            if (watches.isEmpty()) {
                return Collections.emptyList();
            }

            List<AgentSource> result = new ArrayList<>();
            for (WatchInfo watch : watches) {
                log.debug("Fetching snapshot for watch: {} ({})", watch.title(), watch.uuid());
                String snapshot = fetchLatestSnapshot(apiKey, watch.uuid());
                if (snapshot == null || snapshot.isBlank()) {
                    log.debug("Snapshot is null or empty for watch: {}", watch.uuid());
                    continue;
                }
                String snippet = snapshot.length() > 500 ? snapshot.substring(0, 500) + "..." : snapshot;
                result.add(new AgentSource(watch.title(), watch.url(), snippet));
            }
            log.info("Returning {} sources", result.size());
            return result;
        } catch (IOException | InterruptedException e) {
            log.error("Error searching changedetection: {}", e.getMessage(), e);
            Thread.currentThread().interrupt();
            return Collections.emptyList();
        }
    }

    private List<WatchInfo> searchWatches(String apiKey, String query) throws IOException, InterruptedException {
        String trimmed = query == null ? "" : query.trim().toLowerCase();

        // Fetch all watches (or filtered by tag if configured)
        StringBuilder url = new StringBuilder(baseUrl);
        if (!baseUrl.endsWith("/")) {
            url.append('/');
        }
        url.append("api/v1/watch");

        // Add tag filter if configured
        if (defaultTag != null && !defaultTag.isBlank()) {
            url.append("?tag=").append(URLEncoder.encode(defaultTag, StandardCharsets.UTF_8));
        }

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url.toString()))
                .timeout(Duration.ofSeconds(10))
                .header("x-api-key", apiKey)
                .GET()
                .build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        log.info("changedetection API response status: {}", response.statusCode());
        if (response.statusCode() / 100 != 2) {
            log.warn("changedetection API returned non-2xx status: {}, body: {}", response.statusCode(), response.body());
            return Collections.emptyList();
        }

        JsonNode json = mapper.readTree(response.body());
        if (!json.isObject()) {
            return Collections.emptyList();
        }

        // Filter watches client-side by query string matching title or URL
        List<WatchInfo> result = new ArrayList<>();
        Iterator<Map.Entry<String, JsonNode>> fields = json.fields();
        while (fields.hasNext()) {
            Map.Entry<String, JsonNode> entry = fields.next();
            JsonNode watch = entry.getValue();
            String uuid = watch.path("uuid").asText(entry.getKey());
            String urlValue = watch.path("url").asText("");
            String title = watch.path("title").asText(urlValue);
            
            if (urlValue.isEmpty()) {
                continue;
            }

            // If query is provided, filter by matching title or URL (case-insensitive)
            if (!trimmed.isEmpty()) {
                String titleLower = title.toLowerCase();
                String urlLower = urlValue.toLowerCase();
                if (!titleLower.contains(trimmed) && !urlLower.contains(trimmed)) {
                    continue;
                }
            }

            result.add(new WatchInfo(uuid, title, urlValue));
        }

        return result;
    }

    private String fetchLatestSnapshot(String apiKey, String uuid) throws IOException, InterruptedException {
        StringBuilder url = new StringBuilder(baseUrl);
        if (!baseUrl.endsWith("/")) {
            url.append('/');
        }
        url.append("api/v1/watch/").append(uuid).append("/history/latest");

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(url.toString()))
                .timeout(Duration.ofSeconds(15))
                .header("x-api-key", apiKey)
                .GET()
                .build();

        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() / 100 != 2) {
            return null;
        }

        return response.body();
    }

    private record WatchInfo(String uuid, String title, String url) {}
}
