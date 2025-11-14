package com.capstone.absa.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.util.List;

public class PersonaDtos {

    public record PersonaCreateRequest(
            @NotBlank
            @Size(max = 255)
            String name,
            @Size(max = 4000)
            String description
    ) {}

    public record PersonaResponse(
            String id,
            String name,
            String description,
            String createdAt,
            String updatedAt
    ) {}

    public record PersonaListResponse(
            List<PersonaResponse> personas,
            Integer total
    ) {}
}
