# 다중 컨테이너 관리 도구 가이드

## 컨테이너 관리 도구 비교

| 도구 | 타입 | 난이도 | 적합한 사용 사례 |
|------|------|--------|------------------|
| **Portainer** | GUI 관리 도구 | 쉬움 | Docker/Kubernetes 통합 관리, 초보자 친화적 |
| **Dockge** | Compose GUI | 매우 쉬움 | Docker Compose 중심, 빠르고 간단한 관리 |
| **Rancher Desktop** | 데스크톱 K8s | 중간 | 로컬 Kubernetes 개발 환경 |
| **Kubernetes** | 오케스트레이션 | 어려움 | 대규모 프로덕션, 엔터프라이즈 |
| **Docker Swarm** | 오케스트레이션 | 쉬움 | 간단한 클러스터링, Docker 네이티브 |

---

## 1. Portainer (추천: 10개 이상 컨테이너)

### 특징
- **웹 기반 GUI**로 모든 Docker 리소스 관리
- Docker Compose 스택 배포 지원
- 다중 환경(엔드포인트) 관리 가능
- RBAC, 팀 관리 기능
- Kubernetes 클러스터도 관리 가능

### docker-compose.yml

```yaml
version: '3.8'

services:
  portainer:
    image: portainer/portainer-ce:latest
    container_name: portainer
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    ports:
      - "9000:9000"
      - "9443:9443"
      - "8000:8000"  # Edge Agent
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - portainer_data:/data
    networks:
      - microservices
    command: --admin-password-file /tmp/portainer_password
    environment:
      - TZ=Asia/Seoul

volumes:
  portainer_data:

networks:
  microservices:
    external: true
```

### 초기 설정

```bash
# 네트워크 생성
docker network create microservices

# 관리자 비밀번호 생성
echo -n "your_password" | docker run --rm -i portainer/portainer-ce:latest \
  /portainer --admin-password-stdin > /tmp/portainer_password

# Portainer 시작
docker-compose up -d

# 접속: https://localhost:9443
```

### Portainer에서 Compose 스택 배포하기

1. Portainer UI 접속 (https://localhost:9443)
2. **Stacks** → **Add stack** 클릭
3. **Upload** 또는 **Web editor**로 compose 파일 입력
4. 환경 변수 설정
5. **Deploy the stack** 클릭

---

## 2. Dockge (추천: Compose 중심 관리)

### 특징
- **초경량** Compose 관리 도구
- docker run 명령을 compose로 자동 변환
- 실시간 로그 스트리밍
- 개발자 친화적인 UI (Uptime Kuma 개발자 제작)

### docker-compose.yml

```yaml
version: '3.8'

services:
  dockge:
    image: louislam/dockge:latest
    container_name: dockge
    restart: unless-stopped
    ports:
      - "5001:5001"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./dockge/data:/app/data
      - ./stacks:/opt/stacks  # Compose 파일 저장 위치
    environment:
      - DOCKGE_STACKS_DIR=/opt/stacks
      - TZ=Asia/Seoul
    networks:
      - microservices

networks:
  microservices:
    external: true
```

### 사용법

```bash
docker-compose up -d
# 접속: http://localhost:5001
```

---

## 3. 통합 관리 대시보드 구성

### Portainer + Traefik + 모든 서비스

```yaml
version: '3.8'

services:
  # Traefik Reverse Proxy
  traefik:
    image: traefik:latest
    container_name: traefik
    restart: unless-stopped
    command:
      - --api.dashboard=true
      - --providers.docker=true
      - --providers.docker.exposedbydefault=false
      - --entrypoints.web.address=:80
      - --entrypoints.websecure.address=:443
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"  # Dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik/config:/etc/traefik
    networks:
      - microservices
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.dashboard.rule=Host(`traefik.localhost`)"
      - "traefik.http.routers.dashboard.service=api@internal"

  # Portainer
  portainer:
    image: portainer/portainer-ce:latest
    container_name: portainer
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - portainer_data:/data
    networks:
      - microservices
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.portainer.rule=Host(`portainer.localhost`)"
      - "traefik.http.services.portainer.loadbalancer.server.port=9000"

  # Consul
  consul:
    image: hashicorp/consul:latest
    container_name: consul
    restart: unless-stopped
    command: agent -server -ui -bootstrap-expect=1 -client=0.0.0.0
    volumes:
      - consul_data:/consul/data
    networks:
      - microservices
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.consul.rule=Host(`consul.localhost`)"
      - "traefik.http.services.consul.loadbalancer.server.port=8500"

  # Eureka
  eureka:
    image: springcloud/eureka:latest
    container_name: eureka
    restart: unless-stopped
    environment:
      - EUREKA_INSTANCE_HOSTNAME=eureka
      - EUREKA_CLIENT_REGISTER_WITH_EUREKA=false
      - EUREKA_CLIENT_FETCH_REGISTRY=false
    networks:
      - microservices
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.eureka.rule=Host(`eureka.localhost`)"
      - "traefik.http.services.eureka.loadbalancer.server.port=8761"

  # Kong Gateway
  kong:
    image: kong/kong-gateway:latest
    container_name: kong
    restart: unless-stopped
    environment:
      - KONG_DATABASE=off
      - KONG_ADMIN_LISTEN=0.0.0.0:8001
      - KONG_PROXY_ACCESS_LOG=/dev/stdout
      - KONG_ADMIN_ACCESS_LOG=/dev/stdout
    volumes:
      - ./kong/declarative:/kong/declarative:ro
    networks:
      - microservices
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.kong-admin.rule=Host(`kong.localhost`)"
      - "traefik.http.services.kong-admin.loadbalancer.server.port=8001"

  # Jenkins
  jenkins:
    image: jenkins/jenkins:lts
    container_name: jenkins
    restart: unless-stopped
    privileged: true
    user: root
    environment:
      - JAVA_OPTS=-Xmx2g
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - microservices
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.jenkins.rule=Host(`jenkins.localhost`)"
      - "traefik.http.services.jenkins.loadbalancer.server.port=8080"

  # MkDocs
  mkdocs:
    image: squidfunk/mkdocs-material:latest
    container_name: mkdocs
    restart: unless-stopped
    command: serve --dev-addr=0.0.0.0:8000
    volumes:
      - ./docs:/docs
    networks:
      - microservices
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.mkdocs.rule=Host(`docs.localhost`)"
      - "traefik.http.services.mkdocs.loadbalancer.server.port=8000"

volumes:
  portainer_data:
  consul_data:
  jenkins_home:

networks:
  microservices:
    driver: bridge
```

### 접속 URL (hosts 파일 설정 필요)

```bash
# /etc/hosts 또는 C:\Windows\System32\drivers\etc\hosts
127.0.0.1 traefik.localhost
127.0.0.1 portainer.localhost
127.0.0.1 consul.localhost
127.0.0.1 eureka.localhost
127.0.0.1 kong.localhost
127.0.0.1 jenkins.localhost
127.0.0.1 docs.localhost
```

**접속 주소:**
- Traefik Dashboard: http://traefik.localhost:8080
- Portainer: http://portainer.localhost
- Consul: http://consul.localhost
- Eureka: http://eureka.localhost
- Kong Admin: http://kong.localhost
- Jenkins: http://jenkins.localhost
- Docs: http://docs.localhost

---

## 4. Docker Swarm (간단한 오케스트레이션)

### Swarm 초기화

```bash
# Manager 노드 초기화
docker swarm init

# Worker 노드 추가 (다른 서버에서)
docker swarm join --token <TOKEN> <MANAGER-IP>:2377
```

### Stack 배포

```yaml
# stack.yml
version: '3.8'

services:
  consul:
    image: hashicorp/consul:latest
    command: agent -server -ui -bootstrap-expect=1 -client=0.0.0.0
    networks:
      - microservices
    deploy:
      replicas: 3
      placement:
        constraints:
          - node.role == manager

  eureka:
    image: springcloud/eureka:latest
    networks:
      - microservices
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s

networks:
  microservices:
    driver: overlay
```

```bash
# Stack 배포
docker stack deploy -c stack.yml myapp

# 상태 확인
docker stack services myapp
docker stack ps myapp
```

---

## 5. Kubernetes (프로덕션 대규모)

### k3s 설치 (경량 K8s)

```bash
# k3s 설치
curl -sfL https://get.k3s.io | sh -

# kubectl 설정
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER ~/.kube/config
```

### 예시: Consul Deployment

```yaml
# consul-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: consul
spec:
  replicas: 3
  selector:
    matchLabels:
      app: consul
  template:
    metadata:
      labels:
        app: consul
    spec:
      containers:
      - name: consul
        image: hashicorp/consul:latest
        args:
          - "agent"
          - "-server"
          - "-bootstrap-expect=3"
          - "-ui"
        ports:
        - containerPort: 8500
---
apiVersion: v1
kind: Service
metadata:
  name: consul
spec:
  selector:
    app: consul
  ports:
  - port: 8500
    targetPort: 8500
  type: LoadBalancer
```

```bash
kubectl apply -f consul-deployment.yaml
kubectl get pods
kubectl get services
```

---

## 관리 도구 선택 가이드

### 🏆 **초보자 + 10개 이상 컨테이너**: Portainer
- GUI로 모든 것 관리
- Compose 스택 쉽게 배포
- 팀 협업 가능

### ⚡ **개발자 + Compose 중심**: Dockge
- 초경량, 빠른 속도
- Compose 파일 직접 편집
- CLI와 GUI 병행 사용

### 🚀 **중소 규모 프로덕션**: Docker Swarm + Portainer
- 간단한 클러스터링
- Portainer로 Swarm 관리
- 러닝 커브 낮음

### 🏢 **대규모 엔터프라이즈**: Kubernetes + Rancher
- 무제한 확장성
- 고급 오케스트레이션
- 생태계 풍부

---

## 추천 조합

### 시나리오 1: 개발 환경
```
Dockge + Traefik + 개발용 서비스들
```

### 시나리오 2: 소규모 프로덕션
```
Portainer + Docker Swarm + 서비스들
```

### 시나리오 3: 대규모 프로덕션
```
Kubernetes + Rancher + Helm Charts
```

---

## 전체 스택 시작 스크립트

```bash
#!/bin/bash
# start-all.sh

# 네트워크 생성
docker network create microservices

# Portainer 시작
docker-compose -f portainer-compose.yml up -d

# 각 서비스 시작
docker-compose -f consul-compose.yml up -d
docker-compose -f eureka-compose.yml up -d
docker-compose -f kong-compose.yml up -d
docker-compose -f jenkins-compose.yml up -d
docker-compose -f mkdocs-compose.yml up -d

# 상태 확인
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo "✅ All services started!"
echo "🌐 Portainer: https://localhost:9443"
```
