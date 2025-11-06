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
import java.util.UUID;

/**
 * 속성 모델 엔티티
 * 
 * 분석에 사용할 속성 카테고리를 정의합니다.
 * Python 모델: AspectModel (app/db.py)
 */
@Entity
@Table(
    name = "aspect_models",
    indexes = {
        @Index(name = "idx_aspect_model_name", columnList = "name", unique = true),
        @Index(name = "idx_aspect_model_is_active", columnList = "is_active")
    }
)
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AspectModelEntity {

    @Id
    @Column(name = "id", nullable = false, length = 255)
    private String id;

    /**
     * 속성 이름 (예: "수익률", "안정성", "관리비용")
     */
    @Column(name = "name", nullable = false, unique = true, length = 255)
    private String name;

    /**
     * 속성 설명
     */
    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    /**
     * 관련 키워드 리스트
     * PostgreSQL의 JSONB 타입으로 저장
     * 예: ["수익", "이익", "수익률", "수익성"]
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "keywords", columnDefinition = "jsonb")
    private List<String> keywords;

    /**
     * 모델 버전 (예: "v1.0.0")
     */
    @Column(name = "model_version", length = 50)
    private String modelVersion;

    /**
     * 활성화 상태 (1: 활성, 0: 비활성)
     */
    @Column(name = "is_active", nullable = false)
    private Integer isActive;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false, columnDefinition = "TIMESTAMP WITH TIME ZONE")
    private OffsetDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at", columnDefinition = "TIMESTAMP WITH TIME ZONE")
    private OffsetDateTime updatedAt;

    /**
     * 엔티티 생성 전에 ID와 기본값을 설정합니다.
     */
    @PrePersist
    public void prePersist() {
        if (this.id == null) {
            this.id = UUID.randomUUID().toString();
        }
        if (this.isActive == null) {
            this.isActive = 1;
        }
    }
}
