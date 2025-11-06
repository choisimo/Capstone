package com.capstone.absa.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Entity
@Table(name = "absa_analyses", indexes = {
    @Index(name = "idx_absa_content_id", columnList = "contentId"),
    @Index(name = "idx_absa_created_at", columnList = "createdAt")
})
@EntityListeners(AuditingEntityListener.class)
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ABSAAnalysis {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String contentId;

    @Column(columnDefinition = "TEXT", nullable = false)
    private String text;

    @ElementCollection
    @CollectionTable(name = "absa_aspects", joinColumns = @JoinColumn(name = "analysis_id"))
    @Column(name = "aspect")
    private List<String> aspects;

    @Column(columnDefinition = "jsonb")
    @Convert(converter = MapToJsonConverter.class)
    private Map<String, AspectSentimentResult> aspectSentiments;

    @Column(nullable = false)
    private Double overallSentiment;

    @Column(nullable = false)
    private Double confidenceScore;

    @CreatedDate
    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class AspectSentimentResult {
        private Double sentimentScore;
        private String sentimentLabel;
        private Double confidence;
    }
}
