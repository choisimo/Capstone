package com.capstone.absa.controller;

import com.capstone.absa.dto.PersonaDtos.*;
import com.capstone.absa.service.PersonaService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/personas")
@RequiredArgsConstructor
public class PersonaController {

    private final PersonaService service;

    @PostMapping
    public ResponseEntity<PersonaResponse> create(@Valid @RequestBody PersonaCreateRequest request) {
        return ResponseEntity.ok(service.create(request));
    }

    @GetMapping
    public ResponseEntity<List<PersonaResponse>> list() {
        return ResponseEntity.ok(service.listAll());
    }

    @GetMapping("/{id}")
    public ResponseEntity<PersonaResponse> get(@PathVariable String id) {
        return ResponseEntity.ok(service.getById(id));
    }
}
