package com.osint.collector.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.LocalDateTime;
import java.util.Map;

@Entity
@Table(name = "collected_data")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class CollectedData {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "source_id", nullable = false)
    private Long sourceId;
    
    private String title;
    
    @Column(columnDefinition = "TEXT")
    private String content;
    
    private String url;
    
    @Column(name = "published_date")
    private LocalDateTime publishedDate;
    
    @Column(name = "collected_at", nullable = false)
    private LocalDateTime collectedAt;
    
    @Column(name = "content_hash")
    private String contentHash;
    
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "metadata_json", columnDefinition = "jsonb")
    private Map<String, Object> metadataJson;
    
    @Column(nullable = false)
    private Boolean processed = false;
    
    // QA pipeline results
    @Column(name = "http_ok")
    private Boolean httpOk;
    
    @Column(name = "has_content")
    private Boolean hasContent;
    
    private Boolean duplicate;
    
    private Boolean normalized;
    
    @Column(name = "quality_score")
    private Double qualityScore;
    
    @Column(name = "semantic_consistency")
    private Double semanticConsistency;
    
    @Column(name = "outlier_score")
    private Double outlierScore;
    
    @Column(name = "trust_score")
    private Double trustScore;
    
    @PrePersist
    protected void onCreate() {
        collectedAt = LocalDateTime.now();
    }
}
