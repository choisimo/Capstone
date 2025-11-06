package com.capstone.collector.dto;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;

public class CollectionDtos {
    
    public record CollectionRequest(List<Long> source_ids, Boolean force) {}
    
    public record CollectionJob(
            Long id,
            Long source_id,
            String status,
            OffsetDateTime started_at,
            OffsetDateTime completed_at,
            Integer items_collected,
            String error_message,
            OffsetDateTime created_at
    ) {}
    
    public record CollectionStats(
            Integer total_sources,
            Integer active_sources,
            Integer total_items_collected,
            Integer items_collected_today,
            OffsetDateTime last_collection
    ) {}
    
    public record CollectedDataCreate(
            Long source_id,
            String title,
            String content,
            String url,
            OffsetDateTime published_date,
            Map<String, Object> metadata_json
    ) {}
    
    public record CollectedData(
            Long id,
            Long source_id,
            String title,
            String content,
            String url,
            OffsetDateTime published_date,
            OffsetDateTime collected_at,
            String content_hash,
            Map<String, Object> metadata_json,
            Boolean processed,
            Boolean http_ok,
            Boolean has_content,
            Boolean duplicate,
            Boolean normalized,
            Double quality_score,
            Double semantic_consistency,
            Double outlier_score,
            Double trust_score
    ) {}
}
