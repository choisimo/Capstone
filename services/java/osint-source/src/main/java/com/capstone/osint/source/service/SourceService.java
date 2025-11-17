package com.capstone.osint.source.service;

import com.capstone.osint.source.dto.SourceDtos.SourceCreateRequest;
import com.capstone.osint.source.dto.SourceDtos.SourceResponse;
import com.capstone.osint.source.dto.SourceDtos.SourceUpdateRequest;
import jakarta.validation.Valid;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class SourceService {

    private static class SourceModel {
        UUID id;
        String name;
        String url;
        List<String> tags;
        boolean active;
    }

    private final Map<UUID, SourceModel> store = new ConcurrentHashMap<>();

    public SourceResponse create(@Valid SourceCreateRequest req) {
        SourceModel m = new SourceModel();
        m.id = UUID.randomUUID();
        m.name = req.name();
        m.url = req.url();
        m.tags = req.tags() != null ? new ArrayList<>(req.tags()) : List.of();
        m.active = req.active() == null || Boolean.TRUE.equals(req.active());
        store.put(m.id, m);
        return toDto(m);
    }

    public List<SourceResponse> list(Optional<Boolean> activeOnly) {
        return store.values().stream()
                .filter(m -> activeOnly.map(a -> !a || m.active).orElse(true))
                .map(this::toDto)
                .collect(java.util.stream.Collectors.toList());
    }

    public SourceResponse get(UUID id) {
        SourceModel m = store.get(id);
        if (m == null) throw new IllegalArgumentException("Source not found: " + id);
        return toDto(m);
    }

    public SourceResponse update(UUID id, @Valid SourceUpdateRequest req) {
        SourceModel m = store.get(id);
        if (m == null) throw new IllegalArgumentException("Source not found: " + id);
        if (req.name() != null) m.name = req.name();
        if (req.url() != null) m.url = req.url();
        if (req.tags() != null) m.tags = new ArrayList<>(req.tags());
        if (req.active() != null) m.active = req.active();
        return toDto(m);
    }

    public void delete(UUID id) {
        store.remove(id);
    }

    private SourceResponse toDto(SourceModel m) {
        return new SourceResponse(m.id, m.name, m.url, m.tags, m.active);
    }
}
