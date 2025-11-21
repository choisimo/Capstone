package com.capstone.absa.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;

import java.time.OffsetDateTime;

@Entity
@Table(name = "persona_simulations")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PersonaSimulationEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id")
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "persona_id", nullable = false)
    private PersonaEntity persona;

    @Column(name = "scenario_description", nullable = false, columnDefinition = "TEXT")
    private String scenarioDescription;

    @Column(name = "decision", length = 50)
    private String decision;

    @Column(name = "reasoning", columnDefinition = "TEXT")
    private String reasoning;

    @Column(name = "simulated_response", columnDefinition = "TEXT")
    private String simulatedResponse;

    @Column(name = "model_used", length = 50)
    private String modelUsed;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false, columnDefinition = "TIMESTAMP WITH TIME ZONE")
    private OffsetDateTime createdAt;
}
