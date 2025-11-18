package com.capstone.analysis.service;

import com.capstone.analysis.dto.AgentDtos.AgentSearchResponse;
import com.capstone.analysis.dto.AgentDtos.AgentSource;
import com.capstone.analysis.infrastructure.Crawl4aiClient;
import com.capstone.analysis.infrastructure.PerplexityClient;
import com.capstone.analysis.infrastructure.PerplexityClient.PerplexityResult;
import com.capstone.analysis.infrastructure.ChangeDetectionClient;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;

@Service
public class AgentService {

    private final PerplexityClient perplexityClient;
    private final Crawl4aiClient crawl4aiClient;
    private final ChangeDetectionClient changeDetectionClient;

    public AgentService(PerplexityClient perplexityClient,
                        Crawl4aiClient crawl4aiClient,
                        ChangeDetectionClient changeDetectionClient) {
        this.perplexityClient = perplexityClient;
        this.crawl4aiClient = crawl4aiClient;
        this.changeDetectionClient = changeDetectionClient;
    }

    public AgentSearchResponse search(String query) {
        String id = UUID.randomUUID().toString();
        Instant ts = Instant.now();

        CompletableFuture<PerplexityResult> perplexityFuture =
                CompletableFuture.supplyAsync(() -> perplexityClient.query(query));

        CompletableFuture<Optional<AgentSource>> crawlFuture =
                CompletableFuture.supplyAsync(() -> crawl4aiClient.crawlIfUrl(query));

        CompletableFuture<List<AgentSource>> detectionFuture =
                CompletableFuture.supplyAsync(() -> changeDetectionClient.searchLatestChanges(query));

        PerplexityResult perplexity;
        try {
            perplexity = perplexityFuture.join();
        } catch (CompletionException e) {
            throw new IllegalStateException("Perplexity query failed", e.getCause());
        }

        Optional<AgentSource> crawlSource;
        try {
            crawlSource = crawlFuture.join();
        } catch (CompletionException e) {
            crawlSource = Optional.empty();
        }

        List<AgentSource> detectionSources;
        try {
            detectionSources = detectionFuture.join();
        } catch (CompletionException e) {
            detectionSources = List.of();
        }

        List<AgentSource> sources = new ArrayList<>();
        sources.addAll(perplexity.sources());
        crawlSource.ifPresent(sources::add);
        sources.addAll(detectionSources);

        return new AgentSearchResponse(
                id,
                query,
                perplexity.answer(),
                sources,
                perplexity.confidence(),
                ts
        );
    }
}
