# Consul KV Docker Compose 설정

## 단일 노드 개발 환경

```yaml
version: '3.8'

services:
  consul-server:
    image: hashicorp/consul:latest
    container_name: consul-server
    hostname: consul-server
    restart: unless-stopped
    ports:
      - "8500:8500"    # HTTP API & UI
      - "8600:8600/udp" # DNS
      - "8600:8600/tcp" # DNS
    environment:
      CONSUL_BIND_INTERFACE: eth0
      CONSUL_LOCAL_CONFIG: |
        {
          "datacenter": "dc1",
          "data_dir": "/consul/data",
          "log_level": "INFO",
          "server": true,
          "bootstrap_expect": 1,
          "ui_config": {
            "enabled": true
          },
          "connect": {
            "enabled": true
          },
          "client_addr": "0.0.0.0",
          "bind_addr": "0.0.0.0"
        }
    volumes:
      - consul_data:/consul/data
      - ./consul/config:/consul/config
    command: agent -server -ui -bootstrap-expect=1 -client=0.0.0.0
    networks:
      - microservices
    healthcheck:
      test: ["CMD", "consul", "members"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  consul_data:
    driver: local

networks:
  microservices:
    external: true
```

## 3노드 클러스터 프로덕션 환경

```yaml
version: '3.8'

services:
  consul-server-1:
    image: hashicorp/consul:latest
    container_name: consul-server-1
    hostname: consul-server-1
    restart: unless-stopped
    ports:
      - "8500:8500"
      - "8600:8600/udp"
    environment:
      CONSUL_BIND_INTERFACE: eth0
    volumes:
      - consul_data_1:/consul/data
      - ./consul/server1.json:/consul/config/server1.json:ro
    command: agent -server -bootstrap-expect=3 -ui -config-file=/consul/config/server1.json
    networks:
      - microservices
    healthcheck:
      test: ["CMD", "consul", "members"]
      interval: 10s
      timeout: 5s
      retries: 5

  consul-server-2:
    image: hashicorp/consul:latest
    container_name: consul-server-2
    hostname: consul-server-2
    restart: unless-stopped
    environment:
      CONSUL_BIND_INTERFACE: eth0
    volumes:
      - consul_data_2:/consul/data
      - ./consul/server2.json:/consul/config/server2.json:ro
    command: agent -server -bootstrap-expect=3 -config-file=/consul/config/server2.json -retry-join=consul-server-1
    networks:
      - microservices
    depends_on:
      - consul-server-1
    healthcheck:
      test: ["CMD", "consul", "members"]
      interval: 10s
      timeout: 5s
      retries: 5

  consul-server-3:
    image: hashicorp/consul:latest
    container_name: consul-server-3
    hostname: consul-server-3
    restart: unless-stopped
    environment:
      CONSUL_BIND_INTERFACE: eth0
    volumes:
      - consul_data_3:/consul/data
      - ./consul/server3.json:/consul/config/server3.json:ro
    command: agent -server -bootstrap-expect=3 -config-file=/consul/config/server3.json -retry-join=consul-server-1
    networks:
      - microservices
    depends_on:
      - consul-server-1
    healthcheck:
      test: ["CMD", "consul", "members"]
      interval: 10s
      retries: 5

volumes:
  consul_data_1:
  consul_data_2:
  consul_data_3:

networks:
  microservices:
    external: true
```

## 설정 파일 예시 (./consul/server1.json)

```json
{
  "datacenter": "dc1",
  "data_dir": "/consul/data",
  "log_level": "INFO",
  "server": true,
  "bind_addr": "0.0.0.0",
  "client_addr": "0.0.0.0",
  "retry_join": ["consul-server-2", "consul-server-3"],
  "ui_config": {
    "enabled": true
  },
  "connect": {
    "enabled": true
  },
  "ports": {
    "grpc": 8502
  }
}
```

## 초기 데이터 로드 스크립트

```bash
#!/bin/bash
# init-consul-kv.sh

# Consul이 준비될 때까지 대기
until curl -s http://localhost:8500/v1/status/leader | grep -q ":"; do
  echo "Waiting for Consul..."
  sleep 2
done

# KV 데이터 로드
docker exec consul-server consul kv put config/database/host "postgres"
docker exec consul-server consul kv put config/database/port "5432"
docker exec consul-server consul kv put config/app/environment "production"

echo "Consul KV initialized"
```

## 사용 방법

1. 외부 네트워크 생성:
```bash
docker network create microservices
```

2. Consul 시작:
```bash
docker-compose up -d
```

3. UI 접속: http://localhost:8500

4. KV 조회:
```bash
# CLI
docker exec consul-server consul kv get config/app/environment

# HTTP API
curl http://localhost:8500/v1/kv/config/app/environment?raw
```
