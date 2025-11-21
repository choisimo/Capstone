package com.capstone.analysis.controller;

import com.capstone.analysis.config.ColabConfig;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/v1/admin")
public class AdminController {

    private final ColabConfig colabConfig;

    public AdminController(ColabConfig colabConfig) {
        this.colabConfig = colabConfig;
    }

    @PostMapping("/colab-url")
    public ResponseEntity<Map<String, String>> updateColabUrl(@RequestBody Map<String, String> payload) {
        String url = payload.get("url");
        if (url == null || url.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "URL is required"));
        }

        colabConfig.setColabUrl(url);
        return ResponseEntity.ok(Map.of("message", "Colab URL updated successfully", "url", url));
    }

    @GetMapping("/colab-url")
    public ResponseEntity<Map<String, String>> getColabUrl() {
        return ResponseEntity.ok(Map.of("url", colabConfig.getColabUrl()));
    }
}