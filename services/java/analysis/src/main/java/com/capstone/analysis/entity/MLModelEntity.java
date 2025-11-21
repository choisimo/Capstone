package com.capstone.analysis.entity;

import jakarta.persistence.*;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;
import java.time.OffsetDateTime;
import java.util.Map;

@Entity
@Table(name = "ml_models", schema = "analysis")
public class MLModelEntity {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "name", nullable = false)
    private String name;
    
    @Column(name = "version", nullable = false, length = 50)
    private String version;
    
    @Column(name = "model_type", nullable = false, length = 50)
    private String modelType; // sentiment, classification, ner, etc.
    
    @Column(name = "file_path")
    private String filePath;
    
    @Column(name = "is_active", nullable = false)
    private Boolean isActive;
    
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "metrics", columnDefinition = "jsonb")
    private Map<String, Object> metrics;
    
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "hyperparameters", columnDefinition = "jsonb")
    private Map<String, Object> hyperparameters;
    
    @Column(name = "training_job_id")
    private String trainingJobId;
    
    @Column(name = "training_status", length = 20)
    private String trainingStatus; // pending, training, completed, failed
    
    @Column(name = "training_progress")
    private Integer trainingProgress; // 0-100
    
    @Column(name = "trained_at")
    private OffsetDateTime trainedAt;
    
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;
    
    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;
    
    public MLModelEntity() {
    }
    
    public MLModelEntity(String name, String version, String modelType, String filePath) {
        this.name = name;
        this.version = version;
        this.modelType = modelType;
        this.filePath = filePath;
        this.isActive = false;
        this.createdAt = OffsetDateTime.now();
    }
    
    @PrePersist
    protected void onCreate() {
        if (createdAt == null) {
            createdAt = OffsetDateTime.now();
        }
        if (isActive == null) {
            isActive = false;
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
    
    public String getName() {
        return name;
    }
    
    public void setName(String name) {
        this.name = name;
    }
    
    public String getVersion() {
        return version;
    }
    
    public void setVersion(String version) {
        this.version = version;
    }
    
    public String getModelType() {
        return modelType;
    }
    
    public void setModelType(String modelType) {
        this.modelType = modelType;
    }
    
    public String getFilePath() {
        return filePath;
    }
    
    public void setFilePath(String filePath) {
        this.filePath = filePath;
    }
    
    public Boolean getIsActive() {
        return isActive;
    }
    
    public void setIsActive(Boolean isActive) {
        this.isActive = isActive;
    }
    
    public Map<String, Object> getMetrics() {
        return metrics;
    }
    
    public void setMetrics(Map<String, Object> metrics) {
        this.metrics = metrics;
    }
    
    public Map<String, Object> getHyperparameters() {
        return hyperparameters;
    }
    
    public void setHyperparameters(Map<String, Object> hyperparameters) {
        this.hyperparameters = hyperparameters;
    }
    
    public String getTrainingJobId() {
        return trainingJobId;
    }
    
    public void setTrainingJobId(String trainingJobId) {
        this.trainingJobId = trainingJobId;
    }
    
    public String getTrainingStatus() {
        return trainingStatus;
    }
    
    public void setTrainingStatus(String trainingStatus) {
        this.trainingStatus = trainingStatus;
    }
    
    public Integer getTrainingProgress() {
        return trainingProgress;
    }
    
    public void setTrainingProgress(Integer trainingProgress) {
        this.trainingProgress = trainingProgress;
    }
    
    public OffsetDateTime getTrainedAt() {
        return trainedAt;
    }
    
    public void setTrainedAt(OffsetDateTime trainedAt) {
        this.trainedAt = trainedAt;
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
