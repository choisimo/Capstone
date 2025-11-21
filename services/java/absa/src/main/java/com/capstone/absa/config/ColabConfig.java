package com.capstone.absa.config;

import org.springframework.stereotype.Component;

import java.util.concurrent.atomic.AtomicReference;

/**
 * Google Colab 설정 및 URL 관리
 */
@Component
public class ColabConfig {

    private final AtomicReference<String> colabUrl = new AtomicReference<>("");
    private final String apiKey = "capstone-secret-api-key"; // 실제 환경에서는 환경변수나 Vault로 관리

    public String getColabUrl() {
        return colabUrl.get();
    }

    public void setColabUrl(String url) {
        // URL 정규화 (끝에 슬래시 제거)
        if (url != null && url.endsWith("/")) {
            url = url.substring(0, url.length() - 1);
        }
        this.colabUrl.set(url);
    }

    public String getApiKey() {
        return apiKey;
    }

    public boolean isColabAvailable() {
        String url = colabUrl.get();
        return url != null && !url.isEmpty();
    }
}