package com.capstone.collector.dto;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

public class DataSourceDtos {
    public record DataSourceCreate(String name, String url, String source_type, Integer collection_frequency, Map<String, Object> metadata_json) {}
    public record DataSourceUpdate(String name, String url, Boolean is_active, Integer collection_frequency, Map<String, Object> metadata_json) {}
    public record DataSource(UUID id, String name, String url, String source_type, Boolean is_active, OffsetDateTime last_collected, Integer collection_frequency, Map<String, Object> metadata_json, OffsetDateTime created_at, OffsetDateTime updated_at) {}
}