package com.capstone.absa.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * 헬스체크 및 기본 정보 컨트롤러
 */
@RestController
public class HealthController {

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> healthCheck() {
        return ResponseEntity.ok(Map.of(
                "status", "healthy",
                "service", "absa-service"
        ));
    }

    @GetMapping("/")
    public ResponseEntity<Map<String, Object>> root() {
        return ResponseEntity.ok(Map.of(
                "service", "Pension Sentiment ABSA Service",
                "version", "1.0.0",
                "status", "running",
                "endpoints", Map.of(
                        "analysis", "/analysis - ABSA 분석 작업",
                        "health", "/health - 헬스 체크"
                )
        ));
    }
}
