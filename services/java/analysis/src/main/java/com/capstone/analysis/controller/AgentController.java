package com.capstone.analysis.controller;

import com.capstone.analysis.dto.AgentDtos.AgentSearchRequest;
import com.capstone.analysis.dto.AgentDtos.AgentSearchResponse;
import com.capstone.analysis.service.AgentService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/agent")
public class AgentController {

    private final AgentService agentService;

    public AgentController(AgentService agentService) {
        this.agentService = agentService;
    }

    @PostMapping("/search")
    public ResponseEntity<AgentSearchResponse> search(@RequestBody AgentSearchRequest request) {
        AgentSearchResponse response = agentService.search(request.query());
        return ResponseEntity.ok(response);
    }
}
