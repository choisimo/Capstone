package com.capstone.osint.planning;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * OSINT Planning Service
 * 
 * OSINT 계획 및 키워드 관리 서비스입니다.
 * 
 * 주요 기능:
 * - 키워드 확장 및 추천
 * - OSINT 수집 계획 관리
 * - 검색 전략 최적화
 */
@SpringBootApplication
public class OsintPlanningApplication {
    
    public static void main(String[] args) {
        SpringApplication.run(OsintPlanningApplication.class, args);
    }
}
