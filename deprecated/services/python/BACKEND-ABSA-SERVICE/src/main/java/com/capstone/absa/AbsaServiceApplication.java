package com.capstone.absa;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.data.jpa.repository.config.EnableJpaAuditing;

/**
 * ABSA Service 메인 애플리케이션
 * 
 * 속성 기반 감성 분석(Aspect-Based Sentiment Analysis) 서비스입니다.
 * 연금 관련 컨텐츠의 세부 속성별 감성을 분석합니다.
 */
@SpringBootApplication
@EnableDiscoveryClient
@EnableJpaAuditing
public class AbsaServiceApplication {

    public static void main(String[] args) {
        SpringApplication.run(AbsaServiceApplication.class, args);
    }
}
