package com.capstone.osint.source.service.filter;

import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Component
public class FilterRegistry {
    private final Map<String, TextFilter> filtersById = new HashMap<>();

    public FilterRegistry(List<TextFilter> filters) {
        if (filters != null) {
            for (TextFilter f : filters) {
                filtersById.put(f.id(), f);
            }
        }
    }

    public TextFilter get(String id) {
        return filtersById.get(id);
    }

    public Map<String, TextFilter> all() {
        return Map.copyOf(filtersById);
    }
}
