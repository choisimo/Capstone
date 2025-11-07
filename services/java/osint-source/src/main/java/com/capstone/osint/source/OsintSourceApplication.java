package com.capstone.osint.source;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * OSINT Source Service
 * 
 * OSINT 소스 관리 및 발견 서비스입니다.
 * 
 * 주요 기능:
 * - 데이터 소스 등록 및 관리
 * - 소스 발견 및 검증
 * - 소스 모니터링 및 상태 추적
 * - 메트릭 수집 및 보고
 */
@SpringBootApplication
public class OsintSourceApplication {
    
    public static void main(String[] args) {
        SpringApplication.run(OsintSourceApplication.class, args);
    }
}
