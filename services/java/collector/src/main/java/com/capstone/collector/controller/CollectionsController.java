package com.capstone.collector.controller;

import com.capstone.collector.dto.CollectionDtos.*;
import com.capstone.collector.service.CollectionService;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@RestController
@RequestMapping("/collections")
public class CollectionsController {

    private final CollectionService collectionService;

    public CollectionsController(CollectionService collectionService) {
        this.collectionService = collectionService;
    }

    @PostMapping("/start")
    @ResponseStatus(HttpStatus.OK)
    public List<CollectionJob> start(@RequestBody CollectionRequest request) {
        return collectionService.startCollection(request);
    }

    @GetMapping("/stats")
    public CollectionStats stats() {
        return collectionService.getStats();
    }

    @GetMapping("/jobs")
    public List<CollectionJob> jobs(@RequestParam(defaultValue = "0") int skip,
                                    @RequestParam(defaultValue = "100") int limit,
                                    @RequestParam(required = false, name = "status_filter") String statusFilter) {
        return collectionService.getJobs(skip, limit, statusFilter);
    }

    @GetMapping("/jobs/{job_id}")
    public CollectionJob job(@PathVariable("job_id") Long jobId) {
        return collectionService.getJob(jobId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Collection job not found"));
    }

    @GetMapping("/data")
    public List<CollectedData> data(@RequestParam(defaultValue = "0") int skip,
                                    @RequestParam(defaultValue = "100") int limit,
                                    @RequestParam(name = "source_id", required = false) Long sourceId,
                                    @RequestParam(required = false) Boolean processed) {
        return collectionService.getCollectedData(skip, limit, sourceId, processed);
    }

    @PostMapping("/data/{data_id}/process")
    public CollectedData process(@PathVariable("data_id") Long dataId) {
        boolean success = collectionService.markProcessed(dataId);
        if (!success) {
            throw new ResponseStatusException(HttpStatus.NOT_FOUND, "Collected data not found");
        }
        return collectionService.getCollectedData(0, 1, null, null).stream()
                .filter(d -> d.id().equals(dataId))
                .findFirst()
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Collected data not found"));
    }
}
