package com.capstone.collector.entity;

import jakarta.persistence.*;
import java.time.OffsetDateTime;

@Entity
@Table(name = "collected_data", indexes = {
        @Index(name = "idx_content_hash", columnList = "content_hash")
})
public class CollectedDataEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, name = "source_id")
    private Long sourceId;

    @Column(columnDefinition = "TEXT")
    private String title;

    @Column(columnDefinition = "TEXT")
    private String content;

    @Column(columnDefinition = "TEXT")
    private String url;

    @Column(name = "published_date")
    private OffsetDateTime publishedDate;

    @Column(name = "collected_at", nullable = false)
    private OffsetDateTime collectedAt;

    @Column(name = "content_hash", length = 64)
    private String contentHash;

    @Column(name = "metadata_json", columnDefinition = "jsonb")
    @org.hibernate.annotations.JdbcTypeCode(org.hibernate.type.SqlTypes.JSON)
    private String metadataJson;

    @Column(nullable = false)
    private Boolean processed = false;

    @Column(name = "http_ok")
    private Boolean httpOk;

    @Column(name = "has_content")
    private Boolean hasContent;

    @Column(name = "duplicate")
    private Boolean duplicate;

    @Column(name = "normalized")
    private Boolean normalized;

    @Column(name = "quality_score")
    private Double qualityScore;

    @Column(name = "semantic_consistency")
    private Double semanticConsistency;

    @Column(name = "outlier_score")
    private Double outlierScore;

    @Column(name = "trust_score")
    private Double trustScore;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public Long getSourceId() {
        return sourceId;
    }

    public void setSourceId(Long sourceId) {
        this.sourceId = sourceId;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getContent() {
        return content;
    }

    public void setContent(String content) {
        this.content = content;
    }

    public String getUrl() {
        return url;
    }

    public void setUrl(String url) {
        this.url = url;
    }

    public OffsetDateTime getPublishedDate() {
        return publishedDate;
    }

    public void setPublishedDate(OffsetDateTime publishedDate) {
        this.publishedDate = publishedDate;
    }

    public OffsetDateTime getCollectedAt() {
        return collectedAt;
    }

    public void setCollectedAt(OffsetDateTime collectedAt) {
        this.collectedAt = collectedAt;
    }

    public String getContentHash() {
        return contentHash;
    }

    public void setContentHash(String contentHash) {
        this.contentHash = contentHash;
    }

    public String getMetadataJson() {
        return metadataJson;
    }

    public void setMetadataJson(String metadataJson) {
        this.metadataJson = metadataJson;
    }

    public Boolean getProcessed() {
        return processed;
    }

    public void setProcessed(Boolean processed) {
        this.processed = processed;
    }

    public Boolean getHttpOk() {
        return httpOk;
    }

    public void setHttpOk(Boolean httpOk) {
        this.httpOk = httpOk;
    }

    public Boolean getHasContent() {
        return hasContent;
    }

    public void setHasContent(Boolean hasContent) {
        this.hasContent = hasContent;
    }

    public Boolean getDuplicate() {
        return duplicate;
    }

    public void setDuplicate(Boolean duplicate) {
        this.duplicate = duplicate;
    }

    public Boolean getNormalized() {
        return normalized;
    }

    public void setNormalized(Boolean normalized) {
        this.normalized = normalized;
    }

    public Double getQualityScore() {
        return qualityScore;
    }

    public void setQualityScore(Double qualityScore) {
        this.qualityScore = qualityScore;
    }

    public Double getSemanticConsistency() {
        return semanticConsistency;
    }

    public void setSemanticConsistency(Double semanticConsistency) {
        this.semanticConsistency = semanticConsistency;
    }

    public Double getOutlierScore() {
        return outlierScore;
    }

    public void setOutlierScore(Double outlierScore) {
        this.outlierScore = outlierScore;
    }

    public Double getTrustScore() {
        return trustScore;
    }

    public void setTrustScore(Double trustScore) {
        this.trustScore = trustScore;
    }
}
