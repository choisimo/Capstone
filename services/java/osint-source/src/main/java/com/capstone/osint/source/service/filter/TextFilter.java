package com.capstone.osint.source.service.filter;

import java.util.Map;

public interface TextFilter {
    String id();
    String apply(String content, Map<String, Object> config);
}
