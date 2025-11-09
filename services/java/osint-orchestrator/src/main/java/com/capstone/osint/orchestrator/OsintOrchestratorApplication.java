package com.capstone.osint.orchestrator;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * OSINT Orchestrator Service
 * 
 * OSINT 태스크 오케스트레이션 및 이벤트 처리 서비스입니다.
 * 
 * 주요 기능:
 * - Redis Streams 이벤트 소비
 * - 태스크 오케스트레이션 및 스케줄링
 * - 감사 로그 관리 (Postgres)
 * - 메트릭 및 모니터링
 */
@SpringBootApplication
@EnableScheduling
public class OsintOrchestratorApplication {
    
    public static void main(String[] args) {
        SpringApplication.run(OsintOrchestratorApplication.class, args);
    }
}
