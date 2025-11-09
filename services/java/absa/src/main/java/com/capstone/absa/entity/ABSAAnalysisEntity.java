package com.capstone.absa.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/**
 * ABSA 분석 결과 엔티티
 * 
 * 속성별 감성 분석 결과를 저장합니다.
 * Python 모델: ABSAAnalysis (app/db.py)
 */
@Entity
@Table(
    name = "absa_analyses",
    indexes = {
        @Index(name = "idx_absa_content_id", columnList = "content_id"),
        @Index(name = "idx_absa_created_at", columnList = "created_at")
    }
)
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ABSAAnalysisEntity {

    @Id
    @Column(name = "id", nullable = false, length = 255)
    private String id;

    @Column(name = "content_id", length = 255)
    private String contentId;

    @Column(name = "text", columnDefinition = "TEXT")
    private String text;

    /**
     * 추출된 속성 리스트
     * PostgreSQL의 JSONB 타입으로 저장
     * 예: ["수익률", "안정성", "관리비용"]
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "aspects", columnDefinition = "jsonb")
    private List<String> aspects;

    /**
     * 속성별 감성 점수
     * PostgreSQL의 JSONB 타입으로 저장
     * 예: {"수익률": {"sentiment_score": 0.8, "sentiment_label": "positive", "confidence": 0.9}}
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "aspect_sentiments", columnDefinition = "jsonb")
    private Map<String, Map<String, Object>> aspectSentiments;

    /**
     * 전체 감성 점수 (-1.0 ~ 1.0)
     */
    @Column(name = "overall_sentiment")
    private Double overallSentiment;

    /**
     * 신뢰도 점수 (0.0 ~ 1.0)
     */
    @Column(name = "confidence_score")
    private Double confidenceScore;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false, columnDefinition = "TIMESTAMP WITH TIME ZONE")
    private OffsetDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at", columnDefinition = "TIMESTAMP WITH TIME ZONE")
    private OffsetDateTime updatedAt;

    /**
     * 엔티티 생성 전에 ID를 자동으로 생성합니다.
     */
    @PrePersist
    public void prePersist() {
        if (this.id == null) {
            this.id = UUID.randomUUID().toString();
        }
    }
}
