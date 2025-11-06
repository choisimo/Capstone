package com.capstone.collector.dto;

import java.time.OffsetDateTime;
import java.util.List;

public class FeedDtos {
    
    public record FeedInfo(
            String title,
            String link,
            String description,
            String language
    ) {}
    
    public record FeedEntry(
            String title,
            String link,
            String description,
            OffsetDateTime published_date,
            String author
    ) {}
    
    public record ParsedFeed(
            boolean valid,
            FeedInfo feed_info,
            int entry_count,
            List<FeedEntry> sample_entries
    ) {}
    
    public record FeedFetchResult(
            String feed_id,
            String feed_title,
            int items_collected,
            List<FeedEntry> items,
            OffsetDateTime fetched_at
    ) {}
    
    public record FeedListResponse(
            List<FeedSummary> feeds,
            int total
    ) {}
    
    public record FeedSummary(
            Long id,
            String name,
            String url,
            String type,
            boolean is_active,
            OffsetDateTime last_fetched
    ) {}
    
    public record FetchAllResult(
            int total_feeds,
            int success_count,
            int error_count,
            List<FeedFetchResult> results,
            OffsetDateTime executed_at
    ) {}
}
