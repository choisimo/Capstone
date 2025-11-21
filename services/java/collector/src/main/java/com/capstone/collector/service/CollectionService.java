package com.capstone.collector.service;

import com.capstone.collector.dto.CollectionDtos.*;
import com.capstone.collector.entity.CollectionJobEntity;
import com.capstone.collector.entity.CollectedDataEntity;
import com.capstone.collector.entity.DataSourceEntity;
import com.capstone.collector.repository.CollectionJobRepository;
import com.capstone.collector.repository.CollectedDataRepository;
import com.capstone.collector.repository.DataSourceRepository;
import com.capstone.collector.strategy.CollectionStrategy;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
public class CollectionService {
    private static final Logger logger = LoggerFactory.getLogger(CollectionService.class);

    private final CollectionJobRepository jobRepo;
    private final CollectedDataRepository dataRepo;
    private final DataSourceRepository sourceRepo;
    private final ObjectMapper objectMapper;
    private final List<CollectionStrategy> strategies;

    @Value("${collection.min-content-length:100}")
    private int minContentLength;

    public CollectionService(CollectionJobRepository jobRepo,
                             CollectedDataRepository dataRepo,
                             DataSourceRepository sourceRepo,
                             ObjectMapper objectMapper,
                             List<CollectionStrategy> strategies) {
        this.jobRepo = jobRepo;
        this.dataRepo = dataRepo;
        this.sourceRepo = sourceRepo;
        this.objectMapper = objectMapper;
        this.strategies = strategies;
    }

    @Transactional
    public List<CollectionJob> startCollection(CollectionRequest request) {
        List<UUID> sourceIds = request.source_ids();
        if (sourceIds == null || sourceIds.isEmpty()) {
            sourceIds = sourceRepo.findAll().stream()
                    .filter(s -> Boolean.TRUE.equals(s.getIsActive()))
                    .map(DataSourceEntity::getId)
                    .collect(Collectors.toList());
        }

        List<CollectionJob> jobs = sourceIds.stream().map(sid -> {
            CollectionJobEntity jobEntity = new CollectionJobEntity();
            jobEntity.setSourceId(sid);
            jobEntity.setStatus("queued");
            jobEntity.setCreatedAt(OffsetDateTime.now(ZoneOffset.UTC));
            jobEntity.setItemsCollected(0);
            jobEntity = jobRepo.save(jobEntity);
            scheduleCollectionAsync(jobEntity.getId(), sid);
            return toJobDto(jobEntity);
        }).collect(Collectors.toList());

        return jobs;
    }

    @Async
    protected void scheduleCollectionAsync(UUID jobId, UUID sourceId) {
        runCollection(jobId, sourceId);
    }

    @Transactional
    public void runCollection(UUID jobId, UUID sourceId) {
        Optional<CollectionJobEntity> jobOpt = jobRepo.findById(jobId);
        if (jobOpt.isEmpty()) {
            logger.warn("Job not found: {}", jobId);
            return;
        }
        CollectionJobEntity job = jobOpt.get();
        job.setStatus("running");
        job.setStartedAt(OffsetDateTime.now(ZoneOffset.UTC));
        jobRepo.save(job);

        try {
            Optional<DataSourceEntity> sourceOpt = sourceRepo.findById(sourceId);
            if (sourceOpt.isEmpty()) {
                job.setStatus("failed");
                job.setErrorMessage("Source not found");
                job.setCompletedAt(OffsetDateTime.now(ZoneOffset.UTC));
                jobRepo.save(job);
                return;
            }

            DataSourceEntity source = sourceOpt.get();
            int collected = performCollectionForSource(source);

            job.setItemsCollected(collected);
            job.setStatus("completed");
            job.setCompletedAt(OffsetDateTime.now(ZoneOffset.UTC));
            source.setLastCollected(OffsetDateTime.now(ZoneOffset.UTC));
            sourceRepo.save(source);
            jobRepo.save(job);
        } catch (Exception ex) {
            logger.error("Collection failed for job {}", jobId, ex);
            job.setStatus("failed");
            job.setErrorMessage(ex.getMessage());
            job.setCompletedAt(OffsetDateTime.now(ZoneOffset.UTC));
            jobRepo.save(job);
        }
    }

    private int performCollectionForSource(DataSourceEntity source) {
        String type = source.getSourceType();
        logger.info("Collecting from source: {} (type={})", source.getName(), type);

        CollectionStrategy strategy = strategies == null ? null : strategies.stream()
                .filter(s -> s.supports(type))
                .findFirst()
                .orElse(null);

        if (strategy == null) {
            logger.warn("No collection strategy for type: {} (sourceId={})", type, source.getId());
            return 0;
        }
        logger.info("Found strategy {} for type {}", strategy.getClass().getSimpleName(), type);

        try {
            return strategy.collect(source).join();
        } catch (Exception ex) {
            logger.error("Strategy collect failed for source {}: {}", source.getId(), ex.getMessage());
            return 0;
        }
    }

    @Transactional(readOnly = true)
    public CollectionStats getStats() {
        List<CollectedDataEntity> allData = dataRepo.findAll();
        int totalSources = (int) allData.stream().map(CollectedDataEntity::getSourceId).distinct().count();
        int activeSources = (int) sourceRepo.findAll().stream()
                .filter(s -> Boolean.TRUE.equals(s.getIsActive())).count();
        int totalItems = allData.size();

        LocalDate today = LocalDate.now(ZoneOffset.UTC);
        int itemsToday = (int) allData.stream()
                .filter(d -> d.getCollectedAt() != null && d.getCollectedAt().toLocalDate().equals(today))
                .count();

        OffsetDateTime lastCollection = allData.stream()
                .map(CollectedDataEntity::getCollectedAt)
                .max(OffsetDateTime::compareTo)
                .orElse(null);

        return new CollectionStats(totalSources, activeSources, totalItems, itemsToday, lastCollection);
    }

    @Transactional(readOnly = true)
    public List<CollectionJob> getJobs(int skip, int limit, String statusFilter) {
        List<CollectionJobEntity> jobs;
        if (statusFilter != null && !statusFilter.isBlank()) {
            jobs = jobRepo.findByStatus(statusFilter);
        } else {
            jobs = jobRepo.findAll();
        }
        return jobs.stream().skip(skip).limit(limit).map(this::toJobDto).collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public Optional<CollectionJob> getJob(UUID jobId) {
        return jobRepo.findById(jobId).map(this::toJobDto);
    }

    @Transactional(readOnly = true)
    public List<CollectedData> getCollectedData(int skip, int limit, UUID sourceId, Boolean processed) {
        List<CollectedDataEntity> data;
        if (sourceId != null && processed != null) {
            data = dataRepo.findBySourceIdAndProcessed(sourceId, processed);
        } else if (sourceId != null) {
            data = dataRepo.findBySourceId(sourceId);
        } else if (processed != null) {
            data = dataRepo.findByProcessed(processed);
        } else {
            data = dataRepo.findAll();
        }
        return data.stream().skip(skip).limit(limit).map(this::toDataDto).collect(Collectors.toList());
    }

    @Transactional
    public boolean markProcessed(UUID dataId) {
        Optional<CollectedDataEntity> opt = dataRepo.findById(dataId);
        if (opt.isEmpty()) return false;
        CollectedDataEntity entity = opt.get();
        entity.setProcessed(true);
        dataRepo.save(entity);
        return true;
    }

    private CollectionJob toJobDto(CollectionJobEntity e) {
        return new CollectionJob(
                e.getId(), e.getSourceId(), e.getStatus(),
                e.getStartedAt(), e.getCompletedAt(),
                e.getItemsCollected(), e.getErrorMessage(), e.getCreatedAt()
        );
    }

    private CollectedData toDataDto(CollectedDataEntity e) {
        Map<String, Object> metadata = readJson(e.getMetadata());
        return new CollectedData(
                e.getId(), e.getSourceId(), e.getTitle(), e.getContent(), e.getUrl(),
                e.getPublishedAt(), e.getCollectedAt(), e.getContentHash(), metadata, e.getProcessed()
        );
    }

    private Map<String, Object> readJson(String json) {
        if (json == null || json.isBlank()) return null;
        try {
            return objectMapper.readValue(json, new TypeReference<>() {});
        } catch (IOException ex) {
            return null;
        }
    }
}
