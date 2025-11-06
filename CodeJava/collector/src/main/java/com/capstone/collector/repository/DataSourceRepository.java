package com.capstone.collector.repository;

import com.capstone.collector.entity.DataSourceEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface DataSourceRepository extends JpaRepository<DataSourceEntity, Long> {
}
