package com.capstone.collector.service;

import com.capstone.collector.dto.DataSourceDtos.*;
import com.capstone.collector.entity.DataSourceEntity;
import com.capstone.collector.repository.DataSourceRepository;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.time.OffsetDateTime;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Service
public class SourceService {
    private final DataSourceRepository repo;
    private final ObjectMapper objectMapper;

    public SourceService(DataSourceRepository repo, ObjectMapper objectMapper) {
        this.repo = repo;
        this.objectMapper = objectMapper;
    }

    @Transactional
    public DataSource create(DataSourceCreate req) {
        DataSourceEntity e = new DataSourceEntity();
        e.setName(req.name());
        e.setUrl(req.url());
        e.setSourceType(req.source_type());
        e.setIsActive(true);
        e.setCollectionFrequency(Optional.ofNullable(req.collection_frequency()).orElse(3600));
        e.setCreatedAt(OffsetDateTime.now());
        e.setUpdatedAt(OffsetDateTime.now());
        if (req.metadata_json() != null) {
            e.setMetadata(writeJson(req.metadata_json()));
        }
        DataSourceEntity saved = repo.save(e);
        return toDto(saved);
    }

    @Transactional(readOnly = true)
    public java.util.List<DataSource> list(int skip, int limit, Boolean activeOnly) {
        java.util.List<DataSourceEntity> all = repo.findAll();
        return all.stream()
                .filter(e -> activeOnly == null || Boolean.TRUE.equals(e.getIsActive()) == activeOnly)
                .skip(skip)
                .limit(limit)
                .map(this::toDto)
                .toList();
    }

    @Transactional(readOnly = true)
    public DataSource get(UUID id) {
        return repo.findById(id).map(this::toDto).orElse(null);
    }

    @Transactional
    public DataSource update(UUID id, DataSourceUpdate req) {
        return repo.findById(id).map(e -> {
            if (req.name() != null) e.setName(req.name());
            if (req.url() != null) e.setUrl(req.url());
            if (req.is_active() != null) e.setIsActive(req.is_active());
            if (req.collection_frequency() != null) e.setCollectionFrequency(req.collection_frequency());
            if (req.metadata_json() != null) e.setMetadata(writeJson(req.metadata_json()));
            e.setUpdatedAt(OffsetDateTime.now());
            return toDto(repo.save(e));
        }).orElse(null);
    }

    @Transactional
    public boolean delete(UUID id) {
        if (!repo.existsById(id)) return false;
        repo.deleteById(id);
        return true;
    }

    private DataSource toDto(DataSourceEntity e) {
        Map<String, Object> metadata = readJson(e.getMetadata());
        return new DataSource(
                e.getId(), e.getName(), e.getUrl(), e.getSourceType(), e.getIsActive(),
                e.getLastCollected(), e.getCollectionFrequency(), metadata, e.getCreatedAt(), e.getUpdatedAt()
        );
    }

    private String writeJson(Map<String, Object> map) {
        try {
            return objectMapper.writeValueAsString(map);
        } catch (IOException ex) {
            throw new RuntimeException("Failed to serialize metadata_json", ex);
        }
    }

    private Map<String, Object> readJson(String json) {
        if (json == null || json.isBlank()) return null;
        try {
            return objectMapper.readValue(json, new TypeReference<Map<String, Object>>() {});
        } catch (IOException ex) {
            // If corrupted JSON is stored, avoid failing the whole request
            return null;
        }
    }
}
