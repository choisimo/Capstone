package com.capstone.absa.service;

import com.capstone.absa.dto.PersonaDtos.*;
import com.capstone.absa.entity.PersonaEntity;
import com.capstone.absa.exception.PersonaNotFoundException;
import com.capstone.absa.repository.PersonaRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class PersonaService {

    private final PersonaRepository repository;

    @Transactional
    public PersonaResponse create(PersonaCreateRequest req) {
        if (repository.existsByName(req.name())) {
            throw new IllegalArgumentException("Persona with the same name already exists: " + req.name());
        }
        PersonaEntity entity = PersonaEntity.builder()
                .name(req.name())
                .description(req.description())
                .build();
        PersonaEntity saved = repository.save(entity);
        return toResponse(saved);
    }

    @Transactional(readOnly = true)
    public List<PersonaResponse> listAll() {
        return repository.findAll().stream()
                .map(this::toResponse)
                .toList();
    }

    @Transactional(readOnly = true)
    public PersonaResponse getById(String id) {
        PersonaEntity entity = repository.findById(id)
                .orElseThrow(() -> new PersonaNotFoundException(id));
        return toResponse(entity);
    }

    private PersonaResponse toResponse(PersonaEntity e) {
        String createdAt = e.getCreatedAt() != null ? e.getCreatedAt().toString() : null;
        String updatedAt = e.getUpdatedAt() != null ? e.getUpdatedAt().toString() : null;
        return new PersonaResponse(
                e.getId(),
                e.getName(),
                e.getDescription(),
                createdAt,
                updatedAt
        );
    }
}
