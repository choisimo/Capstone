package com.capstone.analysis.entity;

import jakarta.persistence.*;
import java.time.OffsetDateTime;

@Entity
@Table(name = "sentiment_analysis")
public class SentimentAnalysisEntity {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "content_id", nullable = false)
    private String contentId;
    
    @Column(name = "text", columnDefinition = "TEXT")
    private String text;
    
    @Column(name = "sentiment_score", nullable = false)
    private Double sentimentScore;
    
    @Column(name = "sentiment_label", nullable = false, length = 50)
    private String sentimentLabel;
    
    @Column(name = "confidence", nullable = false)
    private Double confidence;
    
    @Column(name = "model_version", length = 50)
    private String modelVersion;
    
    @Column(name = "analyzed_at", nullable = false)
    private OffsetDateTime analyzedAt;
    
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;
    
    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;
    
    public SentimentAnalysisEntity() {
    }
    
    public SentimentAnalysisEntity(String contentId, String text, Double sentimentScore, 
                                   String sentimentLabel, Double confidence, String modelVersion) {
        this.contentId = contentId;
        this.text = text;
        this.sentimentScore = sentimentScore;
        this.sentimentLabel = sentimentLabel;
        this.confidence = confidence;
        this.modelVersion = modelVersion;
        this.analyzedAt = OffsetDateTime.now();
        this.createdAt = OffsetDateTime.now();
    }
    
    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = OffsetDateTime.now();
        }
        if (analyzedAt == null) {
            analyzedAt = OffsetDateTime.now();
        }
    }
    
    @PreUpdate
    protected void onUpdate() {
        updatedAt = OffsetDateTime.now();
    }
    
    // Getters and Setters
    public Long getId() {
        return id;
    }
    
    public void setId(Long id) {
        this.id = id;
    }
    
    public String getContentId() {
        return contentId;
    }
    
    public void setContentId(String contentId) {
        this.contentId = contentId;
    }
    
    public String getText() {
        return text;
    }
    
    public void setText(String text) {
        this.text = text;
    }
    
    public Double getSentimentScore() {
        return sentimentScore;
    }
    
    public void setSentimentScore(Double sentimentScore) {
        this.sentimentScore = sentimentScore;
    }
    
    public String getSentimentLabel() {
        return sentimentLabel;
    }
    
    public void setSentimentLabel(String sentimentLabel) {
        this.sentimentLabel = sentimentLabel;
    }
    
    public Double getConfidence() {
        return confidence;
    }
    
    public void setConfidence(Double confidence) {
        this.confidence = confidence;
    }
    
    public String getModelVersion() {
        return modelVersion;
    }
    
    public void setModelVersion(String modelVersion) {
        this.modelVersion = modelVersion;
    }
    
    public OffsetDateTime getAnalyzedAt() {
        return analyzedAt;
    }
    
    public void setAnalyzedAt(OffsetDateTime analyzedAt) {
        this.analyzedAt = analyzedAt;
    }
    
    public OffsetDateTime getCreatedAt() {
        return createdAt;
    }
    
    public void setCreatedAt(OffsetDateTime createdAt) {
        this.createdAt = createdAt;
    }
    
    public OffsetDateTime getUpdatedAt() {
        return updatedAt;
    }
    
    public void setUpdatedAt(OffsetDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }
}
