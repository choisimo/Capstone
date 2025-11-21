package com.capstone.absa.repository;

import com.capstone.absa.entity.PersonaMemoryEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PersonaMemoryRepository extends JpaRepository<PersonaMemoryEntity, Long> {

    @Query(value = """
        SELECT *
        FROM persona_memories
        WHERE persona_id = :personaId
        ORDER BY embedding <=> CAST(:vector AS vector)
        LIMIT :limit
        """, nativeQuery = true)
    List<PersonaMemoryEntity> findTopSimilarMemories(
            @Param("personaId") String personaId,
            @Param("vector") String vector,
            @Param("limit") int limit
    );
}
