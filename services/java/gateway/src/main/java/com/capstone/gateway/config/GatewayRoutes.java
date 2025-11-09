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

    @Value("${services.absa-url:http://localhost:8083}")
    private String absaUrl;

    @Value("${services.alert-url:http://localhost:8084}")
    private String alertUrl;

    @Value("${services.osint-orchestrator-url:http://localhost:8085}")
    private String osintOrchestratorUrl;

    @Value("${services.osint-planning-url:http://localhost:8086}")
    private String osintPlanningUrl;

    @Value("${services.osint-source-url:http://localhost:8087}")
    private String osintSourceUrl;

    @Bean
    public RouteLocator routes(RouteLocatorBuilder builder) {
        return builder.routes()
                // Collector Service
                .route("collector", r -> r.path("/api/v1/collector/**", "/sources/**", "/collections/**", "/feeds/**")
                        .uri(collectorUrl))
                
                // Analysis Service
                .route("analysis", r -> r.path("/api/v1/analysis/**", "/api/v1/sentiment/**", "/api/v1/trends/**", "/api/v1/reports/**", "/api/v1/models/**")
                        .uri(analysisUrl))
                
                // ABSA Service
                .route("absa", r -> r.path("/api/v1/absa/**", "/aspects/**", "/api/v1/personas/**")
                        .uri(absaUrl))
                
                // Alert Service
                .route("alert", r -> r.path("/api/v1/alerts/**", "/alerts/**", "/rules/**", "/notifications/**")
                        .uri(alertUrl))
                
                // OSINT Orchestrator Service
                .route("osint-orchestrator", r -> r.path("/api/v1/osint-orchestrator/**", "/tasks/**", "/dashboard/**")
                        .uri(osintOrchestratorUrl))
                
                // OSINT Planning Service
                .route("osint-planning", r -> r.path("/api/v1/osint-planning/**", "/api/v1/plans/**")
                        .uri(osintPlanningUrl))
                
                // OSINT Source Service
                .route("osint-source", r -> r.path("/api/v1/osint-source/**", "/api/v1/sources/**")
                        .uri(osintSourceUrl))
                
                .build();
    }
}
