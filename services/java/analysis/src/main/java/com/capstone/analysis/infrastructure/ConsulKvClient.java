package com.capstone.analysis.infrastructure;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Optional;

/**
 * Minimal Consul KV HTTP client.
 *
 * Spring Cloud Consul는 비활성화 상태이므로, 런타임에서 필요한 비밀 값만
 * 직접 HTTP API를 통해 조회합니다.
 */
@Component
public class ConsulKvClient {

    private final HttpClient httpClient;
    private final String consulHost;
    private final int consulPort;
    private final String consulToken;

    public ConsulKvClient(
            @Value("${SPRING_CLOUD_CONSUL_HOST:consul}") String consulHost,
            @Value("${SPRING_CLOUD_CONSUL_PORT:8500}") int consulPort,
            @Value("${CONSUL_HTTP_TOKEN:}") String consulToken
    ) {
        this.httpClient = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(3))
                .build();
        this.consulHost = consulHost;
        this.consulPort = consulPort;
        this.consulToken = consulToken;
    }

    /**
     * Consul KV에서 RAW 값 조회. 존재하지 않거나 오류 시 Optional.empty().
     */
    public Optional<String> getRawValue(String keyPath) {
        String url = String.format("http://%s:%d/v1/kv/%s?raw", consulHost, consulPort, keyPath);
        HttpRequest.Builder builder = HttpRequest.newBuilder()
                .uri(URI.create(url))
                .timeout(Duration.ofSeconds(5))
                .GET();

        if (!consulToken.isBlank()) {
            builder.header("X-Consul-Token", consulToken);
        }

        try {
            HttpResponse<byte[]> response = httpClient.send(builder.build(), HttpResponse.BodyHandlers.ofByteArray());
            if (response.statusCode() == 200) {
                return Optional.of(new String(response.body(), StandardCharsets.UTF_8));
            }
        } catch (IOException | InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return Optional.empty();
    }
}
