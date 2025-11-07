package com.capstone.absa;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * ABSA (Aspect-Based Sentiment Analysis) Service
 * 
 * 속성 기반 감성 분석 서비스입니다.
 * 연금 관련 컨텐츠의 세부 속성별 감성을 분석합니다.
 * 
 * 주요 기능:
 * - 속성 추출 (수익률, 안정성, 관리비용 등)
 * - 속성별 감성 분석
 * - ABSA 모델 관리
 * - 페르소나 분석
 */
@SpringBootApplication
public class AbsaApplication {
    
    public static void main(String[] args) {
        SpringApplication.run(AbsaApplication.class, args);
    }
}
