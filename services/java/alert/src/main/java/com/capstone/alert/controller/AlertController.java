package com.capstone.alert.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.*;

@RestController
@RequestMapping("/api/v1/alerts")
public class AlertController {

    @GetMapping
    public ResponseEntity<List<Map<String, Object>>> list(
            @RequestParam(required = false) Integer limit,
            @RequestParam(required = false) String status
    ) {
        return ResponseEntity.ok(Collections.emptyList());
    }

    @PostMapping("/{id}/acknowledge")
    public ResponseEntity<Void> acknowledge(
            @PathVariable Long id,
            @RequestBody(required = false) Map<String, Object> body
    ) {
        return ResponseEntity.noContent().build();
    }

    @PostMapping("/{id}/resolve")
    public ResponseEntity<Void> resolve(
            @PathVariable Long id,
            @RequestBody(required = false) Map<String, Object> body
    ) {
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/rules")
    public ResponseEntity<List<Map<String, Object>>> rules(
            @RequestParam(required = false) Integer limit,
            @RequestParam(required = false) Boolean enabled
    ) {
        return ResponseEntity.ok(Collections.emptyList());
    }

    @PatchMapping("/rules/{id}")
    public ResponseEntity<Map<String, Object>> toggleRule(
            @PathVariable Long id,
            @RequestBody(required = false) Map<String, Object> body
    ) {
        // minimal stub response with updated rule shape compatible with UI
        Map<String, Object> rule = new HashMap<>();
        rule.put("id", id);
        // if client sent desired state, echo it; otherwise default to true
        boolean isActive = true;
        if (body != null) {
            Object enabled = body.get("enabled");
            if (enabled instanceof Boolean) {
                isActive = (Boolean) enabled;
            }
            Object is_active = body.get("is_active");
            if (is_active instanceof Boolean) {
                isActive = (Boolean) is_active;
            }
        }
        rule.put("is_active", isActive);
        Map<String, Object> response = new HashMap<>();
        response.put("rule", rule);
        return ResponseEntity.ok(response);
    }
}
