# Kong Gateway Docker Compose 설정

## DB-less 모드 (간단한 구성)

```yaml
version: '3.8'

services:
  kong-gateway:
    image: kong/kong-gateway:latest
    container_name: kong-gateway
    hostname: kong
    restart: unless-stopped
    ports:
      - "8000:8000"   # Proxy HTTP
      - "8443:8443"   # Proxy HTTPS
      - "8001:8001"   # Admin API HTTP
      - "8444:8444"   # Admin API HTTPS
      - "8002:8002"   # Kong Manager HTTP
      - "8445:8445"   # Kong Manager HTTPS
    environment:
      KONG_DATABASE: 'off'
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_ADMIN_ERROR_LOG: /dev/stderr
      KONG_ADMIN_LISTEN: '0.0.0.0:8001, 0.0.0.0:8444 ssl'
      KONG_ADMIN_GUI_LISTEN: '0.0.0.0:8002, 0.0.0.0:8445 ssl'
      KONG_DECLARATIVE_CONFIG: /kong/declarative/kong.yml
    volumes:
      - ./kong/declarative:/kong/declarative:ro
      - kong_prefix:/var/run/kong
      - kong_tmp:/tmp
    networks:
      - microservices
    healthcheck:
      test: ["CMD", "kong", "health"]
      interval: 10s
      timeout: 10s
      retries: 5
      start_period: 30s

volumes:
  kong_prefix:
  kong_tmp:

networks:
  microservices:
    external: true
```

## PostgreSQL 사용 (프로덕션 권장)

```yaml
version: '3.8'

services:
  kong-database:
    image: postgres:15-alpine
    container_name: kong-database
    hostname: kong-database
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${KONG_PG_USER:-kong}
      POSTGRES_DB: ${KONG_PG_DATABASE:-kong}
      POSTGRES_PASSWORD: ${KONG_PG_PASSWORD:-kong}
    volumes:
      - kong_data:/var/lib/postgresql/data
    networks:
      - microservices
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "${KONG_PG_USER:-kong}"]
      interval: 10s
      timeout: 5s
      retries: 5

  kong-migration-bootstrap:
    image: kong/kong-gateway:latest
    container_name: kong-migration-bootstrap
    command: kong migrations bootstrap
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: kong-database
      KONG_PG_DATABASE: ${KONG_PG_DATABASE:-kong}
      KONG_PG_USER: ${KONG_PG_USER:-kong}
      KONG_PG_PASSWORD: ${KONG_PG_PASSWORD:-kong}
    networks:
      - microservices
    depends_on:
      kong-database:
        condition: service_healthy
    restart: on-failure

  kong-migration-up:
    image: kong/kong-gateway:latest
    container_name: kong-migration-up
    command: kong migrations up && kong migrations finish
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: kong-database
      KONG_PG_DATABASE: ${KONG_PG_DATABASE:-kong}
      KONG_PG_USER: ${KONG_PG_USER:-kong}
      KONG_PG_PASSWORD: ${KONG_PG_PASSWORD:-kong}
    networks:
      - microservices
    depends_on:
      kong-migration-bootstrap:
        condition: service_completed_successfully
    restart: on-failure

  kong-gateway:
    image: kong/kong-gateway:latest
    container_name: kong-gateway
    hostname: kong
    restart: unless-stopped
    ports:
      - "8000:8000"
      - "8443:8443"
      - "8001:8001"
      - "8444:8444"
      - "8002:8002"
      - "8445:8445"
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: kong-database
      KONG_PG_DATABASE: ${KONG_PG_DATABASE:-kong}
      KONG_PG_USER: ${KONG_PG_USER:-kong}
      KONG_PG_PASSWORD: ${KONG_PG_PASSWORD:-kong}
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_ADMIN_ERROR_LOG: /dev/stderr
      KONG_ADMIN_LISTEN: '0.0.0.0:8001, 0.0.0.0:8444 ssl'
      KONG_ADMIN_GUI_LISTEN: '0.0.0.0:8002, 0.0.0.0:8445 ssl'
      KONG_PROXY_LISTEN: '0.0.0.0:8000, 0.0.0.0:8443 ssl'
    networks:
      - microservices
    depends_on:
      kong-migration-up:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD", "kong", "health"]
      interval: 10s
      timeout: 10s
      retries: 5
      start_period: 30s

volumes:
  kong_data:

networks:
  microservices:
    external: true
```

## Kong + Konga (GUI 관리 도구)

```yaml
version: '3.8'

services:
  kong-database:
    image: postgres:15-alpine
    container_name: kong-database
    hostname: kong-database
    restart: unless-stopped
    environment:
      POSTGRES_USER: kong
      POSTGRES_DB: kong
      POSTGRES_PASSWORD: kongpass
    volumes:
      - kong_data:/var/lib/postgresql/data
    networks:
      - microservices
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "kong"]
      interval: 10s
      timeout: 5s
      retries: 5

  kong-migration:
    image: kong/kong-gateway:latest
    container_name: kong-migration
    command: kong migrations bootstrap
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: kong-database
      KONG_PG_DATABASE: kong
      KONG_PG_USER: kong
      KONG_PG_PASSWORD: kongpass
    networks:
      - microservices
    depends_on:
      kong-database:
        condition: service_healthy
    restart: on-failure

  kong-gateway:
    image: kong/kong-gateway:latest
    container_name: kong-gateway
    hostname: kong
    restart: unless-stopped
    ports:
      - "8000:8000"
      - "8443:8443"
      - "8001:8001"
      - "8444:8444"
    environment:
      KONG_DATABASE: postgres
      KONG_PG_HOST: kong-database
      KONG_PG_DATABASE: kong
      KONG_PG_USER: kong
      KONG_PG_PASSWORD: kongpass
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_ADMIN_ERROR_LOG: /dev/stderr
      KONG_ADMIN_LISTEN: '0.0.0.0:8001'
      KONG_ADMIN_GUI_URL: 'http://localhost:8002'
    networks:
      - microservices
    depends_on:
      kong-migration:
        condition: service_completed_successfully
    healthcheck:
      test: ["CMD", "kong", "health"]
      interval: 10s
      timeout: 10s
      retries: 5

  konga-database:
    image: postgres:15-alpine
    container_name: konga-database
    restart: unless-stopped
    environment:
      POSTGRES_USER: konga
      POSTGRES_DB: konga
      POSTGRES_PASSWORD: kongapass
    volumes:
      - konga_data:/var/lib/postgresql/data
    networks:
      - microservices
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "konga"]
      interval: 10s
      timeout: 5s
      retries: 5

  konga:
    image: pantsel/konga:latest
    container_name: konga
    restart: unless-stopped
    ports:
      - "1337:1337"
    environment:
      DB_ADAPTER: postgres
      DB_HOST: konga-database
      DB_DATABASE: konga
      DB_USER: konga
      DB_PASSWORD: kongapass
      NODE_ENV: production
      KONGA_HOOK_TIMEOUT: 120000
    networks:
      - microservices
    depends_on:
      konga-database:
        condition: service_healthy
      kong-gateway:
        condition: service_healthy

volumes:
  kong_data:
  konga_data:

networks:
  microservices:
    external: true
```

## Declarative 설정 파일 (./kong/declarative/kong.yml)

```yaml
_format_version: "3.0"
_transform: true

services:
  - name: example-service
    url: http://example-backend:8080
    routes:
      - name: example-route
        paths:
          - /api/example
        strip_path: true
        methods:
          - GET
          - POST
    plugins:
      - name: rate-limiting
        config:
          minute: 100
          policy: local
      - name: cors
        config:
          origins:
            - "*"
          methods:
            - GET
            - POST
            - PUT
            - DELETE
          headers:
            - Accept
            - Content-Type
          credentials: true
          max_age: 3600

  - name: user-service
    url: http://user-service:8080
    routes:
      - name: user-route
        paths:
          - /api/users
        strip_path: false
    plugins:
      - name: jwt
        config:
          secret_is_base64: false
      - name: request-transformer
        config:
          add:
            headers:
              - "X-Gateway:Kong"

plugins:
  - name: prometheus
    config:
      per_consumer: false

upstreams:
  - name: backend-cluster
    targets:
      - target: backend-1:8080
        weight: 100
      - target: backend-2:8080
        weight: 100
```

## .env 파일

```bash
# PostgreSQL 설정
KONG_PG_USER=kong
KONG_PG_PASSWORD=your_secure_password
KONG_PG_DATABASE=kong

# Konga 설정
KONGA_PG_USER=konga
KONGA_PG_PASSWORD=your_konga_password
KONGA_PG_DATABASE=konga
```

## Kong 설정 명령어

```bash
# 서비스 등록
curl -i -X POST http://localhost:8001/services \
  --data name=example-service \
  --data url='http://example.com'

# 라우트 추가
curl -i -X POST http://localhost:8001/services/example-service/routes \
  --data 'paths[]=/api' \
  --data name=example-route

# 플러그인 추가 (Rate Limiting)
curl -i -X POST http://localhost:8001/services/example-service/plugins \
  --data name=rate-limiting \
  --data config.minute=100

# 전체 서비스 조회
curl http://localhost:8001/services

# Health check
curl http://localhost:8001/status
```

## 마이크로서비스 통합 예시

```yaml
version: '3.8'

services:
  kong-gateway:
    image: kong/kong-gateway:latest
    # ... (위의 설정 참조)
    
  user-service:
    build: ./services/user-service
    container_name: user-service
    networks:
      - microservices
    environment:
      SERVICE_PORT: 8080

  order-service:
    build: ./services/order-service
    container_name: order-service
    networks:
      - microservices
    environment:
      SERVICE_PORT: 8080

networks:
  microservices:
    external: true
```

## 사용 방법

1. **네트워크 생성**:
```bash
docker network create microservices
```

2. **환경 변수 설정**:
```bash
cp .env.example .env
# .env 파일 수정
```

3. **Kong 시작**:
```bash
docker-compose up -d
```

4. **관리 UI 접속**:
   - Kong Manager: http://localhost:8002
   - Konga: http://localhost:1337

5. **서비스 테스트**:
```bash
curl http://localhost:8000/api/example
```
