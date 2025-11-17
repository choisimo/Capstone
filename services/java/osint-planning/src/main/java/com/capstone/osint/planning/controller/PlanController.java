package com.capstone.osint.planning.controller;

import com.capstone.osint.planning.dto.PlanDtos.PlanCreateRequest;
import com.capstone.osint.planning.dto.PlanDtos.PlanResponse;
import com.capstone.osint.planning.dto.PlanDtos.PlanUpdateStatusRequest;
import com.capstone.osint.planning.service.PlanService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URI;
import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/osint-planning/plans")
public class PlanController {

    private final PlanService planService;

    public PlanController(PlanService planService) {
        this.planService = planService;
    }

    @PostMapping
    public ResponseEntity<PlanResponse> create(@RequestBody @Valid PlanCreateRequest req) {
        PlanResponse created = planService.create(req);
        return ResponseEntity.created(URI.create("/api/v1/osint-planning/plans/" + created.id()))
                .body(created);
    }

    @GetMapping
    public ResponseEntity<List<PlanResponse>> list() {
        return ResponseEntity.ok(planService.list());
    }

    @GetMapping("/{id}")
    public ResponseEntity<PlanResponse> get(@PathVariable UUID id) {
        return ResponseEntity.ok(planService.get(id));
    }

    @PatchMapping("/{id}/status")
    public ResponseEntity<PlanResponse> updateStatus(@PathVariable UUID id,
                                                     @RequestBody @Valid PlanUpdateStatusRequest req) {
        return ResponseEntity.ok(planService.updateStatus(id, req));
    }
}
