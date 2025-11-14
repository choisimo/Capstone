package com.capstone.osint.source.controller;

import com.capstone.osint.source.dto.FilterDtos.ApplyRequest;
import com.capstone.osint.source.dto.FilterDtos.ApplyResponse;
import com.capstone.osint.source.dto.FilterDtos.CrawlAndFilterRequest;
import com.capstone.osint.source.dto.FilterDtos.CrawlAndFilterResponse;
import com.capstone.osint.source.service.CrawlService;
import com.capstone.osint.source.service.FilterPipelineService;
import com.capstone.osint.source.service.PerplexityService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/sources/filters")
public class FilterController {

    private final FilterPipelineService pipelineService;
    private final CrawlService crawlService;
    private final PerplexityService perplexityService;

    public FilterController(FilterPipelineService pipelineService,
                            CrawlService crawlService,
                            PerplexityService perplexityService) {
        this.pipelineService = pipelineService;
        this.crawlService = crawlService;
        this.perplexityService = perplexityService;
    }

    @PostMapping("/apply")
    public ResponseEntity<ApplyResponse> apply(@RequestBody @Valid ApplyRequest request) {
        return ResponseEntity.ok(pipelineService.apply(request));
    }

    @PostMapping("/crawl-and-apply")
    public ResponseEntity<CrawlAndFilterResponse> crawlAndApply(@RequestBody @Valid CrawlAndFilterRequest request) {
        String crawled = crawlService.fetch(request.url());
        String finalContent = pipelineService.apply(new ApplyRequest(crawled, request.steps())).finalContent();
        if (Boolean.TRUE.equals(request.usePerplexity())) {
            finalContent = perplexityService.enrich(finalContent, request.perplexityQuery());
        }
        return ResponseEntity.ok(new CrawlAndFilterResponse(request.url(), crawled, finalContent));
    }
}
