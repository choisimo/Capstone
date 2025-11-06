package com.capstone.gateway.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class GatewayRoutes {

    @Value("${services.collector-url:http://localhost:8091}")
    private String collectorUrl;

    @Value("${services.analysis-url:http://localhost:8092}")
    private String analysisUrl;

    @Bean
    public RouteLocator routes(RouteLocatorBuilder builder) {
        return builder.routes()
                .route("collector", r -> r.path("/sources/**", "/collections/**", "/feeds/**")
                        .uri(collectorUrl))
                .route("analysis", r -> r.path("/api/v1/sentiment/**", "/api/v1/trends/**", "/api/v1/reports/**", "/api/v1/models/**", "/health")
                        .uri(analysisUrl))
                .build();
    }
}
