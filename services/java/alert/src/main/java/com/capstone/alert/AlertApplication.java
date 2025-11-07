package com.capstone.alert;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Alert Service
 * 
 * 알림 및 통지 서비스입니다.
 * 
 * 주요 기능:
 * - 알림 규칙 관리
 * - 이메일/SMS 발송
 * - 알림 히스토리 관리
 * - 스케줄링 알림
 */
@SpringBootApplication
@EnableScheduling
public class AlertApplication {
    
    public static void main(String[] args) {
        SpringApplication.run(AlertApplication.class, args);
    }
}
