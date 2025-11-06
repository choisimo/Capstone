package com.capstone.collector.entity;

import jakarta.persistence.*;
import java.time.OffsetDateTime;
import java.util.Map;

@Entity
@Table(name = "data_sources")
public class DataSourceEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String name;
    private String url;
    private String sourceType;
    private Boolean isActive;
    private OffsetDateTime lastCollected;
    private Integer collectionFrequency;
    @Column(columnDefinition = "jsonb")
    private String metadataJson; // store as JSON string; map in service
    private OffsetDateTime createdAt;
    private OffsetDateTime updatedAt;

    // getters/setters omitted for brevity
    public Long getId() {return id;}
    public void setId(Long id) {this.id = id;}
    public String getName() {return name;}
    public void setName(String name) {this.name = name;}
    public String getUrl() {return url;}
    public void setUrl(String url) {this.url = url;}
    public String getSourceType() {return sourceType;}
    public void setSourceType(String sourceType) {this.sourceType = sourceType;}
    public Boolean getIsActive() {return isActive;}
    public void setIsActive(Boolean isActive) {this.isActive = isActive;}
    public OffsetDateTime getLastCollected() {return lastCollected;}
    public void setLastCollected(OffsetDateTime lastCollected) {this.lastCollected = lastCollected;}
    public Integer getCollectionFrequency() {return collectionFrequency;}
    public void setCollectionFrequency(Integer collectionFrequency) {this.collectionFrequency = collectionFrequency;}
    public String getMetadataJson() {return metadataJson;}
    public void setMetadataJson(String metadataJson) {this.metadataJson = metadataJson;}
    public OffsetDateTime getCreatedAt() {return createdAt;}
    public void setCreatedAt(OffsetDateTime createdAt) {this.createdAt = createdAt;}
    public OffsetDateTime getUpdatedAt() {return updatedAt;}
    public void setUpdatedAt(OffsetDateTime updatedAt) {this.updatedAt = updatedAt;}
}