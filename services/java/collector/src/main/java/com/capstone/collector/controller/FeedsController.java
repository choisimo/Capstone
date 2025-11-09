package com.capstone.collector.controller;

import com.capstone.collector.dto.FeedDtos.*;
import com.capstone.collector.service.FeedService;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import java.util.Map;

@RestController
@RequestMapping("/feeds")
public class FeedsController {

    private final FeedService feedService;

    public FeedsController(FeedService feedService) {
        this.feedService = feedService;
    }

    @GetMapping("/")
    public FeedListResponse list() {
        return feedService.listFeeds();
    }

    @PostMapping("/fetch/{feed_id}")
    public FeedFetchResult fetch(@PathVariable("feed_id") Long feedId) {
        return feedService.fetchFeed(feedId);
    }

    @PostMapping("/fetch-all")
    public FetchAllResult fetchAll() {
        return feedService.fetchAll();
    }

    @PostMapping("/parse-url")
    public ParsedFeed parseUrl(@RequestBody Map<String, String> request) {
        String url = request.get("url");
        if (url == null || url.isBlank()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "URL is required");
        }
        return feedService.parseUrl(url);
    }
}
