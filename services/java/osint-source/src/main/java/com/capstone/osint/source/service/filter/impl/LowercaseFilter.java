package com.capstone.osint.source.service.filter.impl;

import com.capstone.osint.source.service.filter.TextFilter;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class LowercaseFilter implements TextFilter {
    @Override
    public String id() { return "lowercase"; }

    @Override
    public String apply(String content, Map<String, Object> config) {
        return content == null ? null : content.toLowerCase();
    }
}
