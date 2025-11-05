# Eureka Server Docker Compose 설정

## 단일 Eureka 서버 (개발 환경)

```yaml
version: '3.8'

services:
  eureka-server:
    image: springcloud/eureka:latest
    container_name: eureka-server
    hostname: eureka-server
    restart: unless-stopped
    ports:
      - "8761:8761"
    environment:
      # Spring 설정
      SPRING_APPLICATION_NAME: discovery-server
      SERVER_PORT: 8761
      
      # Eureka 서버 설정
      EUREKA_INSTANCE_HOSTNAME: eureka-server
      EUREKA_INSTANCE_PREFER_IP_ADDRESS: "true"
      EUREKA_CLIENT_REGISTER_WITH_EUREKA: "false"
      EUREKA_CLIENT_FETCH_REGISTRY: "false"
      EUREKA_CLIENT_SERVICEURL_DEFAULTZONE: http://eureka-server:8761/eureka/
      
      # 성능 최적화
      EUREKA_SERVER_ENABLE_SELF_PRESERVATION: "true"
      EUREKA_SERVER_EVICTION_INTERVAL_TIMER_IN_MS: 60000
      EUREKA_SERVER_RENEWAL_THRESHOLD_UPDATE_INTERVAL_MS: 900000
      
      # 로깅
      LOGGING_LEVEL_COM_NETFLIX_EUREKA: INFO
      LOGGING_LEVEL_COM_NETFLIX_DISCOVERY: INFO
    networks:
      - microservices
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8761/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    volumes:
      - eureka_data:/var/lib/eureka

volumes:
  eureka_data:

networks:
  microservices:
    external: true
```

## 커스텀 이미지 빌드용 Dockerfile

```dockerfile
# Dockerfile
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# 타임존 설정
ENV TZ=Asia/Seoul
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# JAR 파일 복사
COPY target/eureka-server-*.jar app.jar

# Health check용 curl 설치
RUN apk add --no-cache curl

# 비root 유저 생성
RUN addgroup -g 1000 spring && \
    adduser -u 1000 -G spring -s /bin/sh -D spring
USER spring:spring

EXPOSE 8761

ENTRYPOINT ["java", \
    "-Djava.security.egd=file:/dev/./urandom", \
    "-XX:+UseContainerSupport", \
    "-XX:MaxRAMPercentage=75.0", \
    "-jar", \
    "app.jar"]
```

## application.yml 설정

```yaml
server:
  port: 8761

spring:
  application:
    name: discovery-server

eureka:
  instance:
    hostname: ${EUREKA_INSTANCE_HOSTNAME:localhost}
    prefer-ip-address: true
    lease-renewal-interval-in-seconds: 30
    lease-expiration-duration-in-seconds: 90
  client:
    register-with-eureka: false
    fetch-registry: false
    service-url:
      defaultZone: http://${eureka.instance.hostname}:${server.port}/eureka/
  server:
    enable-self-preservation: true
    eviction-interval-timer-in-ms: 60000
    renewal-threshold-update-interval-ms: 900000
    wait-time-in-ms-when-sync-empty: 0

management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics
  endpoint:
    health:
      show-details: always
```

## 고가용성 Eureka 클러스터 (3노드)

```yaml
version: '3.8'

services:
  eureka-server-1:
    build:
      context: ./eureka-server
      dockerfile: Dockerfile
    container_name: eureka-server-1
    hostname: eureka-server-1
    restart: unless-stopped
    ports:
      - "8761:8761"
    environment:
      SERVER_PORT: 8761
      EUREKA_INSTANCE_HOSTNAME: eureka-server-1
      EUREKA_INSTANCE_PREFER_IP_ADDRESS: "true"
      EUREKA_CLIENT_REGISTER_WITH_EUREKA: "true"
      EUREKA_CLIENT_FETCH_REGISTRY: "true"
      EUREKA_CLIENT_SERVICEURL_DEFAULTZONE: http://eureka-server-2:8762/eureka/,http://eureka-server-3:8763/eureka/
    networks:
      - microservices
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8761/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  eureka-server-2:
    build:
      context: ./eureka-server
      dockerfile: Dockerfile
    container_name: eureka-server-2
    hostname: eureka-server-2
    restart: unless-stopped
    ports:
      - "8762:8762"
    environment:
      SERVER_PORT: 8762
      EUREKA_INSTANCE_HOSTNAME: eureka-server-2
      EUREKA_INSTANCE_PREFER_IP_ADDRESS: "true"
      EUREKA_CLIENT_REGISTER_WITH_EUREKA: "true"
      EUREKA_CLIENT_FETCH_REGISTRY: "true"
      EUREKA_CLIENT_SERVICEURL_DEFAULTZONE: http://eureka-server-1:8761/eureka/,http://eureka-server-3:8763/eureka/
    networks:
      - microservices
    depends_on:
      - eureka-server-1
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8762/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  eureka-server-3:
    build:
      context: ./eureka-server
      dockerfile: Dockerfile
    container_name: eureka-server-3
    hostname: eureka-server-3
    restart: unless-stopped
    ports:
      - "8763:8763"
    environment:
      SERVER_PORT: 8763
      EUREKA_INSTANCE_HOSTNAME: eureka-server-3
      EUREKA_INSTANCE_PREFER_IP_ADDRESS: "true"
      EUREKA_CLIENT_REGISTER_WITH_EUREKA: "true"
      EUREKA_CLIENT_FETCH_REGISTRY: "true"
      EUREKA_CLIENT_SERVICEURL_DEFAULTZONE: http://eureka-server-1:8761/eureka/,http://eureka-server-2:8762/eureka/
    networks:
      - microservices
    depends_on:
      - eureka-server-1
      - eureka-server-2
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8763/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

networks:
  microservices:
    external: true
```

## 클라이언트 서비스 등록 예시

```yaml
version: '3.8'

services:
  user-service:
    build: ./user-service
    container_name: user-service
    restart: unless-stopped
    environment:
      SPRING_APPLICATION_NAME: user-service
      EUREKA_CLIENT_SERVICEURL_DEFAULTZONE: http://eureka-server:8761/eureka/
      EUREKA_INSTANCE_PREFER_IP_ADDRESS: "true"
      EUREKA_INSTANCE_LEASE_RENEWAL_INTERVAL_IN_SECONDS: 30
      EUREKA_INSTANCE_LEASE_EXPIRATION_DURATION_IN_SECONDS: 90
    networks:
      - microservices
    depends_on:
      eureka-server:
        condition: service_healthy

networks:
  microservices:
    external: true
```

## 사용 방법

1. **네트워크 생성**:
```bash
docker network create microservices
```

2. **Eureka 서버 시작**:
```bash
docker-compose up -d
```

3. **대시보드 접속**: 
   - http://localhost:8761

4. **서비스 등록 확인**:
```bash
curl http://localhost:8761/eureka/apps
```

5. **특정 서비스 조회**:
```bash
curl http://localhost:8761/eureka/apps/USER-SERVICE
```

## 트러블슈팅

### 서비스가 등록되지 않는 경우
- 컨테이너 네트워크 확인
- `eureka.client.serviceUrl.defaultZone` 설정 확인
- 컨테이너 이름/호스트명으로 통신 가능한지 확인

### Self-preservation 모드
- 개발 환경에서는 비활성화 가능: `EUREKA_SERVER_ENABLE_SELF_PRESERVATION: "false"`
