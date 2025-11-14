package com.capstone.collector.strategy;

import com.capstone.collector.entity.DataSourceEntity;
import com.capstone.collector.dto.FeedDtos.FeedFetchResult;
import com.capstone.collector.service.FeedService;
import com.capstone.collector.util.VirtualExecutors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.net.URI;
import java.util.Map;
import java.util.concurrent.*;

@Component
public class RssCollectionStrategy implements CollectionStrategy {

    private static final Logger log = LoggerFactory.getLogger(RssCollectionStrategy.class);

    private final FeedService feedService;
    private final ExecutorService executor;
    private final ConcurrentHashMap<String, Semaphore> domainLimiters = new ConcurrentHashMap<>();

    @Value("${collector.rss.max-concurrent-per-domain:2}")
    private int maxConcurrentPerDomain;

    public RssCollectionStrategy(FeedService feedService) {
        this.feedService = feedService;
        this.executor = VirtualExecutors.newVirtualPerTaskOrCached();
    }

    @Override
    public boolean supports(String sourceType) {
        return "rss".equalsIgnoreCase(sourceType);
    }

    @Override
    public CompletableFuture<Integer> collect(DataSourceEntity source) {
        return CompletableFuture.supplyAsync(() -> {
            String domain = extractDomain(source.getUrl());
            Semaphore limiter = domainLimiters.computeIfAbsent(domain, d -> new Semaphore(maxConcurrentPerDomain));
            try {
                limiter.acquire();
                FeedFetchResult result = feedService.fetchFeed(source.getId());
                return result.items_collected();
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                return 0;
            } catch (Exception ex) {
                log.error("RSS collect failed for source {}: {}", source.getId(), ex.getMessage());
                return 0;
            } finally {
                limiter.release();
            }
        }, executor);
    }

    private String extractDomain(String url) {
        try {
            URI u = URI.create(url);
            return u.getHost() != null ? u.getHost() : "unknown";
        } catch (Exception e) {
            return "unknown";
        }
    }
}
