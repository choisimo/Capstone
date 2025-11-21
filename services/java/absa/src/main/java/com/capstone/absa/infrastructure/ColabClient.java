package com.capstone.absa.infrastructure;

import com.capstone.absa.config.ColabConfig;
import com.capstone.absa.dto.AnalysisDtos.AnalyzeRequest;
import com.capstone.absa.dto.AnalysisDtos.AnalyzeResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;

@Component
@Slf4j
public class ColabClient {

    private final ColabConfig colabConfig;
    private final WebClient webClient;

    public ColabClient(ColabConfig colabConfig, WebClient.Builder webClientBuilder) {
        this.colabConfig = colabConfig;
        this.webClient = webClientBuilder.build();
    }

    /**
     * Colab 서버에 ABSA 분석 요청
     */
    public AnalyzeResponse analyzeABSA(AnalyzeRequest request) {
        if (!colabConfig.isColabAvailable()) {
            log.warn("Colab URL is not configured. Skipping Colab analysis.");
            throw new IllegalStateException("Colab URL not configured");
        }

        String url = colabConfig.getColabUrl() + "/absa";
        log.info("Sending ABSA analysis request to Colab: {}", url);

        try {
            return webClient.post()
                    .uri(url)
                    .header("X-API-KEY", colabConfig.getApiKey())
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(request)
                    .retrieve()
                    .bodyToMono(AnalyzeResponse.class)
                    .timeout(Duration.ofSeconds(10)) // ABSA는 시간이 더 걸릴 수 있으므로 10초
                    .block();
        } catch (Exception e) {
            log.error("Failed to call Colab API: {}", e.getMessage());
            throw new RuntimeException("Colab API call failed", e);
        }
    }
}