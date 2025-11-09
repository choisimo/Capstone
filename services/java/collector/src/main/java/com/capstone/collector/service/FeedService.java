package com.capstone.collector.service;

import com.capstone.collector.dto.FeedDtos.*;
import com.capstone.collector.entity.DataSourceEntity;
import com.capstone.collector.repository.DataSourceRepository;
import com.rometools.rome.feed.synd.SyndEntry;
import com.rometools.rome.feed.synd.SyndFeed;
import com.rometools.rome.io.SyndFeedInput;
import com.rometools.rome.io.XmlReader;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.net.URL;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.ZoneOffset;
import java.util.Date;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class FeedService {
    private static final Logger logger = LoggerFactory.getLogger(FeedService.class);
    
    private final DataSourceRepository sourceRepo;
    
    public FeedService(DataSourceRepository sourceRepo) {
        this.sourceRepo = sourceRepo;
    }
    
    @Transactional(readOnly = true)
    public FeedListResponse listFeeds() {
        List<DataSourceEntity> sources = sourceRepo.findAll().stream()
                .filter(s -> "rss".equalsIgnoreCase(s.getSourceType()))
                .collect(Collectors.toList());
        
        List<FeedSummary> feeds = sources.stream()
                .map(s -> new FeedSummary(
                        s.getId(),
                        s.getName(),
                        s.getUrl(),
                        s.getSourceType(),
                        Boolean.TRUE.equals(s.getIsActive()),
                        s.getLastCollected()
                ))
                .collect(Collectors.toList());
        
        return new FeedListResponse(feeds, feeds.size());
    }
    
    public ParsedFeed parseUrl(String url) {
        try {
            SyndFeed feed = parseFeed(url);
            
            FeedInfo feedInfo = new FeedInfo(
                    feed.getTitle(),
                    feed.getLink(),
                    feed.getDescription(),
                    feed.getLanguage()
            );
            
            List<FeedEntry> entries = feed.getEntries().stream()
                    .limit(5)
                    .map(this::toFeedEntry)
                    .collect(Collectors.toList());
            
            return new ParsedFeed(true, feedInfo, feed.getEntries().size(), entries);
        } catch (Exception ex) {
            logger.error("Failed to parse feed: {}", url, ex);
            return new ParsedFeed(false, null, 0, List.of());
        }
    }
    
    @Transactional
    public FeedFetchResult fetchFeed(Long feedId) {
        DataSourceEntity source = sourceRepo.findById(feedId)
                .orElseThrow(() -> new RuntimeException("Feed not found"));
        
        try {
            SyndFeed feed = parseFeed(source.getUrl());
            
            List<FeedEntry> entries = feed.getEntries().stream()
                    .map(this::toFeedEntry)
                    .collect(Collectors.toList());
            
            source.setLastCollected(OffsetDateTime.now(ZoneOffset.UTC));
            sourceRepo.save(source);
            
            return new FeedFetchResult(
                    String.valueOf(feedId),
                    feed.getTitle(),
                    entries.size(),
                    entries,
                    OffsetDateTime.now(ZoneOffset.UTC)
            );
        } catch (Exception ex) {
            logger.error("Failed to fetch feed: {}", feedId, ex);
            return new FeedFetchResult(
                    String.valueOf(feedId),
                    source.getName(),
                    0,
                    List.of(),
                    OffsetDateTime.now(ZoneOffset.UTC)
            );
        }
    }
    
    @Transactional
    public FetchAllResult fetchAll() {
        List<DataSourceEntity> feeds = sourceRepo.findAll().stream()
                .filter(s -> "rss".equalsIgnoreCase(s.getSourceType()))
                .filter(s -> Boolean.TRUE.equals(s.getIsActive()))
                .collect(Collectors.toList());
        
        int successCount = 0;
        int errorCount = 0;
        List<FeedFetchResult> results = new java.util.ArrayList<>();
        
        for (DataSourceEntity feed : feeds) {
            try {
                FeedFetchResult result = fetchFeed(feed.getId());
                results.add(result);
                if (result.items_collected() > 0) {
                    successCount++;
                } else {
                    errorCount++;
                }
            } catch (Exception ex) {
                logger.error("Failed to fetch feed: {}", feed.getId(), ex);
                errorCount++;
            }
        }
        
        return new FetchAllResult(
                feeds.size(),
                successCount,
                errorCount,
                results,
                OffsetDateTime.now(ZoneOffset.UTC)
        );
    }
    
    private SyndFeed parseFeed(String url) throws Exception {
        SyndFeedInput input = new SyndFeedInput();
        return input.build(new XmlReader(new URL(url)));
    }
    
    private FeedEntry toFeedEntry(SyndEntry entry) {
        OffsetDateTime publishedDate = null;
        if (entry.getPublishedDate() != null) {
            publishedDate = convertToOffsetDateTime(entry.getPublishedDate());
        } else if (entry.getUpdatedDate() != null) {
            publishedDate = convertToOffsetDateTime(entry.getUpdatedDate());
        }
        
        String description = "";
        if (entry.getDescription() != null) {
            description = entry.getDescription().getValue();
        }
        
        String author = "";
        if (entry.getAuthor() != null) {
            author = entry.getAuthor();
        }
        
        return new FeedEntry(
                entry.getTitle(),
                entry.getLink(),
                description,
                publishedDate,
                author
        );
    }
    
    private OffsetDateTime convertToOffsetDateTime(Date date) {
        return date.toInstant()
                .atZone(ZoneId.systemDefault())
                .toOffsetDateTime();
    }
}
