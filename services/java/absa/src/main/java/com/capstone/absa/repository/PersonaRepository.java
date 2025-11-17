package com.capstone.absa.repository;

import com.capstone.absa.entity.PersonaEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface PersonaRepository extends JpaRepository<PersonaEntity, String> {
    Optional<PersonaEntity> findByName(String name);
    boolean existsByName(String name);
}
