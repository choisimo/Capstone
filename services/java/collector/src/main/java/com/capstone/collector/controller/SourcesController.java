package com.capstone.collector.controller;

import com.capstone.collector.dto.DataSourceDtos.*;
import com.capstone.collector.service.SourceService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/sources")
public class SourcesController {
    private final SourceService service;

    public SourcesController(SourceService service) {
        this.service = service;
    }

    @PostMapping("/")
    @ResponseStatus(HttpStatus.CREATED)
    public DataSource create(@Valid @RequestBody DataSourceCreate req) {
        return service.create(req);
    }

    @GetMapping("/")
    public List<DataSource> list(@RequestParam(defaultValue = "0") int skip,
                                 @RequestParam(defaultValue = "100") int limit,
                                 @RequestParam(required = false) Boolean active_only) {
        return service.list(skip, limit, active_only);
    }

    @GetMapping("/{source_id}")
    public DataSource get(@PathVariable("source_id") Long id) {
        DataSource res = service.get(id);
        if (res == null) throw new org.springframework.web.server.ResponseStatusException(HttpStatus.NOT_FOUND, "Data source not found");
        return res;
    }

    @PutMapping("/{source_id}")
    public DataSource update(@PathVariable("source_id") Long id, @Valid @RequestBody DataSourceUpdate req) {
        DataSource res = service.update(id, req);
        if (res == null) throw new org.springframework.web.server.ResponseStatusException(HttpStatus.NOT_FOUND, "Data source not found");
        return res;
    }

    @DeleteMapping("/{source_id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable("source_id") Long id) {
        boolean ok = service.delete(id);
        if (!ok) throw new org.springframework.web.server.ResponseStatusException(HttpStatus.NOT_FOUND, "Data source not found");
    }

    @PostMapping("/{source_id}/test")
    public java.util.Map<String, Object> test(@PathVariable("source_id") Long id) {
        // Placeholder to keep API parity
        DataSource ds = service.get(id);
        if (ds == null) throw new org.springframework.web.server.ResponseStatusException(HttpStatus.NOT_FOUND, "Data source not found");
        return java.util.Map.of("ok", true, "source_id", id);
    }
}
