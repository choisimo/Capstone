package com.capstone.analysis.infrastructure;

import com.capstone.analysis.config.ColabConfig;
import com.capstone.analysis.dto.SentimentDtos.SentimentAnalysisRequest;
import com.capstone.analysis.dto.SentimentDtos.SentimentAnalysisResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatusCode;
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
     * Colab 서버에 감성 분석 요청
     */
    public SentimentAnalysisResponse analyzeSentiment(SentimentAnalysisRequest request) {
        if (!colabConfig.isColabAvailable()) {
            log.warn("Colab URL is not configured. Skipping Colab analysis.");
            throw new IllegalStateException("Colab URL not configured");
        }

        String url = colabConfig.getColabUrl() + "/sentiment";
        log.info("Sending sentiment analysis request to Colab: {}", url);

        try {
            return webClient.post()
                    .uri(url)
                    .header("X-API-KEY", colabConfig.getApiKey())
                    .contentType(MediaType.APPLICATION_JSON)
                    .bodyValue(request)
                    .retrieve()
                    .onStatus(HttpStatusCode::is4xxClientError, clientResponse ->
                            Mono.error(new RuntimeException("Client error: " + clientResponse.statusCode())))
                    .onStatus(HttpStatusCode::is5xxServerError, clientResponse ->
                            Mono.error(new RuntimeException("Server error: " + clientResponse.statusCode())))
                    .bodyToMono(SentimentAnalysisResponse.class)
                    .timeout(Duration.ofSeconds(5)) // 5초 타임아웃
                    .block(); // 동기 처리 (필요시 비동기로 변경 가능)
        } catch (Exception e) {
            log.error("Failed to call Colab API: {}", e.getMessage());
            throw new RuntimeException("Colab API call failed", e);
        }
    }
}