package com.capstone.collector.strategy;

import com.capstone.collector.entity.CollectedDataEntity;
import com.capstone.collector.entity.DataSourceEntity;
import com.capstone.collector.repository.CollectedDataRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.HexFormat;
import java.util.concurrent.CompletableFuture;

@Component
public class Crawl4aiCollectionStrategy implements CollectionStrategy {

    private static final Logger log = LoggerFactory.getLogger(Crawl4aiCollectionStrategy.class);

    private final CollectedDataRepository dataRepo;
    private final ObjectMapper mapper = new ObjectMapper();

    @Value("${crawl4ai.url:http://crawl4ai:8001}")
    private String crawl4aiUrl;

    @Value("${collection.min-content-length:100}")
    private int minContentLength;

    public Crawl4aiCollectionStrategy(CollectedDataRepository dataRepo) {
        this.dataRepo = dataRepo;
    }

    @Override
    public boolean supports(String sourceType) {
        return "crawl4ai_api".equalsIgnoreCase(sourceType) || "html".equalsIgnoreCase(sourceType);
    }

    @Override
    public CompletableFuture<Integer> collect(DataSourceEntity source) {
        return CompletableFuture.supplyAsync(() -> doCollect(source));
    }

    private int doCollect(DataSourceEntity source) {
        log.info("Crawl4ai strategy starting collection for source {} (url: {})", source.getId(), source.getUrl());
        try {
            String endpoint = crawl4aiUrl.endsWith("/") ? crawl4aiUrl + "crawl" : crawl4aiUrl + "/crawl";
            log.info("Calling crawl4ai endpoint: {}", endpoint);
            HttpClient client = HttpClient.newBuilder()
                    .version(HttpClient.Version.HTTP_1_1)
                    .build();
            String body = mapper.createObjectNode()
                    .put("url", source.getUrl())
                    .put("js_render", true)
                    .toString();
            log.info("Request body: {}", body);
            HttpRequest req = HttpRequest.newBuilder(URI.create(endpoint))
                    .header("Content-Type", "application/json")
                    .header("Accept", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(body, StandardCharsets.UTF_8))
                    .build();
            HttpResponse<String> resp = client.send(req, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            if (resp.statusCode() / 100 != 2) {
                log.warn("crawl4ai non-2xx for source {}: status {}, response: {}", source.getId(), resp.statusCode(), resp.body());
                return 0;
            }
            JsonNode json = mapper.readTree(resp.body());
            String content = null;
            if (json.has("markdown") && !json.get("markdown").isNull()) {
                content = json.get("markdown").asText();
            } else if (json.has("html") && !json.get("html").isNull()) {
                content = json.get("html").asText();
            }
            if (content == null) {
                log.warn("crawl4ai returned empty content for source {}", source.getId());
                return 0;
            }
            String trimmed = content.strip();
            if (trimmed.length() < minContentLength) {
                log.debug("content below threshold ({} chars) for source {}", trimmed.length(), source.getId());
                return 0;
            }

            CollectedDataEntity e = new CollectedDataEntity();
            e.setSourceId(source.getId());
            e.setTitle(null);
            e.setContent(trimmed);
            e.setUrl(source.getUrl());
            e.setPublishedAt(null);
            e.setCollectedAt(OffsetDateTime.now(ZoneOffset.UTC));
            e.setContentHash(sha256(trimmed));
            e.setMetadata(null);
            e.setProcessed(false);

            dataRepo.save(e);
            return 1;
        } catch (Exception ex) {
            log.error("crawl4ai collect failed for source {}: {}", source.getId(), ex.toString());
            return 0;
        }
    }

    private String sha256(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest(input.getBytes(StandardCharsets.UTF_8));
            return HexFormat.of().formatHex(digest);
        } catch (Exception e) {
            return null;
        }
    }
}
