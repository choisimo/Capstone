package com.capstone.analysis.infrastructure;

import com.capstone.analysis.config.ColabConfig;
import com.capstone.analysis.dto.TrainingDtos.TrainRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import java.time.Duration;

@Component
@RequiredArgsConstructor
@Slf4j
public class ColabTrainingClient {

    private final ColabConfig colabConfig;
    private final WebClient.Builder webClientBuilder;

    public void requestTraining(TrainRequest request) {
        if (!colabConfig.isColabAvailable()) {
            log.warn("Colab URL is not configured. Skipping training request.");
            throw new IllegalStateException("Colab URL not configured");
        }

        String url = colabConfig.getColabUrl() + "/train";
        WebClient client = webClientBuilder.build();

        client.post()
                .uri(url)
                .header("X-API-KEY", colabConfig.getApiKey())
                .contentType(MediaType.APPLICATION_JSON)
                .bodyValue(request)
                .retrieve()
                .bodyToMono(Void.class)
                .timeout(Duration.ofSeconds(10))
                .onErrorResume(e -> {
                    log.error("Failed to send training job {} to Colab: {}", request.jobId(), e.getMessage());
                    return Mono.empty();
                })
                .subscribe();
    }
}
