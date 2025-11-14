package com.capstone.osint.source.service.filter.impl;

import com.capstone.osint.source.service.filter.TextFilter;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class RegexReplaceFilter implements TextFilter {
    @Override
    public String id() { return "regex_replace"; }

    @Override
    public String apply(String content, Map<String, Object> config) {
        if (content == null) return null;
        Object pattern = config != null ? config.get("pattern") : null;
        Object replacement = config != null ? config.get("replacement") : null;
        if (pattern == null || replacement == null) return content;
        return content.replaceAll(pattern.toString(), replacement.toString());
    }
}
