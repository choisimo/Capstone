package com.capstone.analysis.entity;

import jakarta.persistence.*;
import java.time.OffsetDateTime;

@Entity
@Table(name = "trend_data")
public class TrendDataEntity {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "entity", nullable = false)
    private String entity;
    
    @Column(name = "period", nullable = false, length = 20)
    private String period; // daily, weekly, monthly
    
    @Column(name = "date", nullable = false)
    private OffsetDateTime date;
    
    @Column(name = "sentiment_score", nullable = false)
    private Double sentimentScore;
    
    @Column(name = "volume", nullable = false)
    private Integer volume;
    
    @Column(name = "keywords", columnDefinition = "TEXT[]")
    private String[] keywords;
    
    @Column(name = "trend_direction", length = 20)
    private String trendDirection; // up, down, stable
    
    @Column(name = "trend_strength")
    private Double trendStrength;
    
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;
    
    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;
    
    public TrendDataEntity() {
    }
    
    public TrendDataEntity(String entity, String period, OffsetDateTime date, 
                           Double sentimentScore, Integer volume) {
        this.entity = entity;
        this.period = period;
        this.date = date;
        this.sentimentScore = sentimentScore;
        this.volume = volume;
        this.createdAt = OffsetDateTime.now();
    }
    
    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = OffsetDateTime.now();
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
    
    public String getEntity() {
        return entity;
    }
    
    public void setEntity(String entity) {
        this.entity = entity;
    }
    
    public String getPeriod() {
        return period;
    }
    
    public void setPeriod(String period) {
        this.period = period;
    }
    
    public OffsetDateTime getDate() {
        return date;
    }
    
    public void setDate(OffsetDateTime date) {
        this.date = date;
    }
    
    public Double getSentimentScore() {
        return sentimentScore;
    }
    
    public void setSentimentScore(Double sentimentScore) {
        this.sentimentScore = sentimentScore;
    }
    
    public Integer getVolume() {
        return volume;
    }
    
    public void setVolume(Integer volume) {
        this.volume = volume;
    }
    
    public String[] getKeywords() {
        return keywords;
    }
    
    public void setKeywords(String[] keywords) {
        this.keywords = keywords;
    }
    
    public String getTrendDirection() {
        return trendDirection;
    }
    
    public void setTrendDirection(String trendDirection) {
        this.trendDirection = trendDirection;
    }
    
    public Double getTrendStrength() {
        return trendStrength;
    }
    
    public void setTrendStrength(Double trendStrength) {
        this.trendStrength = trendStrength;
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
