package com.capstone.osint.source.controller;

import com.capstone.osint.source.dto.SourceDtos.SourceCreateRequest;
import com.capstone.osint.source.dto.SourceDtos.SourceResponse;
import com.capstone.osint.source.dto.SourceDtos.SourceUpdateRequest;
import com.capstone.osint.source.service.SourceService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/sources")
public class SourceController {

    private final SourceService sourceService;

    public SourceController(SourceService sourceService) {
        this.sourceService = sourceService;
    }

    @PostMapping
    public ResponseEntity<SourceResponse> create(@RequestBody @Valid SourceCreateRequest req) {
        SourceResponse created = sourceService.create(req);
        return ResponseEntity.created(URI.create("/api/v1/sources/" + created.id())).body(created);
    }

    @GetMapping
    public ResponseEntity<List<SourceResponse>> list(@RequestParam(name = "active_only", required = false) Boolean activeOnly) {
        return ResponseEntity.ok(sourceService.list(Optional.ofNullable(activeOnly)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<SourceResponse> get(@PathVariable UUID id) {
        return ResponseEntity.ok(sourceService.get(id));
    }

    @PutMapping("/{id}")
    public ResponseEntity<SourceResponse> update(@PathVariable UUID id, @RequestBody @Valid SourceUpdateRequest req) {
        return ResponseEntity.ok(sourceService.update(id, req));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable UUID id) {
        sourceService.delete(id);
        return ResponseEntity.noContent().build();
    }
}
