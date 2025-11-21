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
import java.util.Map;
import java.util.UUID;

@Entity
@Table(
    name = "personas",
    indexes = {
        @Index(name = "idx_persona_name", columnList = "name")
    }
)
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PersonaEntity {

    @Id
    @Column(name = "id", nullable = false, length = 255)
    private String id;

    @Column(name = "name", length = 255)
    private String name;

    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    // --- DPSP persona profiling fields ---

    /**
     * 외부 사이트의 사용자 ID 또는 해시 (예: 커뮤니티 닉네임, 유저 ID)
     */
    @Column(name = "external_id", length = 255)
    private String externalId;

    /**
     * 해당 페르소나가 처음 수집된 대표 URL (provenance)
     */
    @Column(name = "source_url", columnDefinition = "TEXT")
    private String sourceUrl;

    /**
     * 페르소나를 2~3줄로 요약한 설명
     */
    @Column(name = "summary", columnDefinition = "TEXT")
    private String summary;

    /**
     * 심리/성격 특성 (예: OCEAN 점수, 가치관 등)
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "psychology_traits", columnDefinition = "jsonb")
    private Map<String, Object> psychologyTraits;

    /**
     * 커뮤니케이션 스타일 (말투, 자주 쓰는 표현 등)
     */
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "communication_style", columnDefinition = "jsonb")
    private Map<String, Object> communicationStyle;

    /**
     * 마지막으로 프로파일링이 수행된 시각
     */
    @Column(name = "last_profiled_at", columnDefinition = "TIMESTAMP WITH TIME ZONE")
    private OffsetDateTime lastProfiledAt;

    /**
     * 이 페르소나와 연결된 벡터 컬렉션 ID (예: 외부 벡터 DB 컬렉션 이름)
     */
    @Column(name = "embedding_collection_id", length = 255)
    private String embeddingCollectionId;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false, columnDefinition = "TIMESTAMP WITH TIME ZONE")
    private OffsetDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at", columnDefinition = "TIMESTAMP WITH TIME ZONE")
    private OffsetDateTime updatedAt;

    @PrePersist
    public void prePersist() {
        if (this.id == null) {
            this.id = UUID.randomUUID().toString();
        }
    }
}
