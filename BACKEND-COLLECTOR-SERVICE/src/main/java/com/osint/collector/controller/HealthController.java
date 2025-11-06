package com.osint.collector.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.http.ResponseEntity;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequiredArgsConstructor
public class HealthController {
    
    private final JdbcTemplate jdbcTemplate;
    private final RedisTemplate<String, Object> redisTemplate;
    
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "healthy");
        response.put("service", "collector-service");
        return ResponseEntity.ok(response);
    }
    
    @GetMapping("/ready")
    public ResponseEntity<Map<String, Object>> ready() {
        Map<String, Object> response = new HashMap<>();
        Map<String, Boolean> dependencies = new HashMap<>();
        
        // Check PostgreSQL
        try {
            jdbcTemplate.queryForObject("SELECT 1", Integer.class);
            dependencies.put("db", true);
        } catch (Exception e) {
            dependencies.put("db", false);
        }
        
        // Check Redis
        try {
            redisTemplate.getConnectionFactory().getConnection().ping();
            dependencies.put("redis", true);
        } catch (Exception e) {
            dependencies.put("redis", false);
        }
        
        boolean ready = dependencies.values().stream().allMatch(v -> v);
        response.put("ready", ready);
        response.put("dependencies", dependencies);
        
        if (!ready) {
            return ResponseEntity.status(503).body(response);
        }
        
        return ResponseEntity.ok(response);
    }
    
    @GetMapping("/")
    public ResponseEntity<Map<String, Object>> root() {
        Map<String, Object> response = new HashMap<>();
        response.put("service", "Pension Sentiment Collector Service");
        response.put("version", "1.0.0");
        response.put("status", "running");
        
        Map<String, String> endpoints = new HashMap<>();
        endpoints.put("sources", "/sources - Manage data sources");
        endpoints.put("collections", "/collections - Data collection operations");
        endpoints.put("feeds", "/feeds - RSS feed management");
        endpoints.put("health", "/health - Health check");
        endpoints.put("ready", "/ready - Readiness check");
        
        response.put("endpoints", endpoints);
        return ResponseEntity.ok(response);
    }
}
