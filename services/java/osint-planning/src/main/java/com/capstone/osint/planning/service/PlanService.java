package com.capstone.osint.planning.service;

import com.capstone.osint.planning.dto.PlanDtos.PlanCreateRequest;
import com.capstone.osint.planning.dto.PlanDtos.PlanResponse;
import com.capstone.osint.planning.dto.PlanDtos.PlanUpdateStatusRequest;
import jakarta.validation.Valid;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class PlanService {

    private static class PlanModel {
        UUID id;
        String name;
        List<String> goals;
        List<String> constraints;
        String status;
    }

    private final Map<UUID, PlanModel> store = new ConcurrentHashMap<>();

    public PlanResponse create(@Valid PlanCreateRequest req) {
        PlanModel m = new PlanModel();
        m.id = UUID.randomUUID();
        m.name = req.name();
        m.goals = req.goals() != null ? new ArrayList<>(req.goals()) : List.of();
        m.constraints = req.constraints() != null ? new ArrayList<>(req.constraints()) : List.of();
        m.status = "DRAFT";
        store.put(m.id, m);
        return toDto(m);
    }

    public List<PlanResponse> list() {
        return store.values().stream().map(this::toDto).collect(java.util.stream.Collectors.toList());
    }

    public PlanResponse get(UUID id) {
        PlanModel m = store.get(id);
        if (m == null) throw new IllegalArgumentException("Plan not found: " + id);
        return toDto(m);
    }

    public PlanResponse updateStatus(UUID id, @Valid PlanUpdateStatusRequest req) {
        PlanModel m = store.get(id);
        if (m == null) throw new IllegalArgumentException("Plan not found: " + id);
        m.status = req.status();
        return toDto(m);
    }

    private PlanResponse toDto(PlanModel m) {
        return new PlanResponse(m.id, m.name, m.goals, m.constraints, m.status);
    }
}
