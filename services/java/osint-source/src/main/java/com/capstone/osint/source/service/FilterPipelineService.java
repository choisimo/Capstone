package com.capstone.osint.source.service;

import com.capstone.osint.source.dto.FilterDtos.ApplyRequest;
import com.capstone.osint.source.dto.FilterDtos.ApplyResponse;
import com.capstone.osint.source.dto.FilterDtos.FilterStep;
import com.capstone.osint.source.service.filter.FilterRegistry;
import com.capstone.osint.source.service.filter.TextFilter;
import org.springframework.stereotype.Service;

@Service
public class FilterPipelineService {

    private final FilterRegistry registry;

    public FilterPipelineService(FilterRegistry registry) {
        this.registry = registry;
    }

    public ApplyResponse apply(ApplyRequest request) {
        String content = request.content();
        if (request.steps() != null) {
            for (FilterStep step : request.steps()) {
                TextFilter f = registry.get(step.filterId());
                if (f == null) {
                    throw new IllegalArgumentException("Unknown filter: " + step.filterId());
                }
                content = f.apply(content, step.config());
            }
        }
        return new ApplyResponse(request.content(), content);
    }
}
