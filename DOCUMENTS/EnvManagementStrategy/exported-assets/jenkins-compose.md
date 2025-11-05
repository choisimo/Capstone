# Jenkins Docker Compose 설정

## 기본 Jenkins with Persistent Data

```yaml
version: '3.8'

services:
  jenkins:
    image: jenkins/jenkins:lts
    container_name: jenkins
    hostname: jenkins
    restart: unless-stopped
    privileged: true
    user: root
    ports:
      - "8080:8080"   # Web UI
      - "50000:50000" # Agent 통신 포트
    environment:
      - JENKINS_OPTS=--prefix=/jenkins
      - JAVA_OPTS=-Djenkins.install.runSetupWizard=false -Xmx2g -Xms512m
      - TZ=Asia/Seoul
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
      - /usr/bin/docker:/usr/bin/docker
    networks:
      - microservices
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/login"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 90s

volumes:
  jenkins_home:
    driver: local

networks:
  microservices:
    external: true
```

## Jenkins with Docker-in-Docker (DinD)

```yaml
version: '3.8'

services:
  jenkins-docker:
    image: docker:dind
    container_name: jenkins-docker
    privileged: true
    restart: unless-stopped
    environment:
      - DOCKER_TLS_CERTDIR=/certs
    volumes:
      - jenkins_docker_certs:/certs/client
      - jenkins_data:/var/jenkins_home
    networks:
      microservices:
        aliases:
          - docker
    command: --storage-driver=overlay2

  jenkins:
    image: jenkins/jenkins:lts
    container_name: jenkins
    restart: unless-stopped
    user: root
    ports:
      - "8080:8080"
      - "50000:50000"
    environment:
      - DOCKER_HOST=tcp://docker:2376
      - DOCKER_CERT_PATH=/certs/client
      - DOCKER_TLS_VERIFY=1
      - JAVA_OPTS=-Xmx2048m -Xms1024m
      - TZ=Asia/Seoul
    volumes:
      - jenkins_data:/var/jenkins_home
      - jenkins_docker_certs:/certs/client:ro
    networks:
      - microservices
    depends_on:
      - jenkins-docker
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/login"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 90s

volumes:
  jenkins_data:
  jenkins_docker_certs:

networks:
  microservices:
    external: true
```

## 커스텀 Jenkins 이미지 (플러그인 사전 설치)

### Dockerfile

```dockerfile
FROM jenkins/jenkins:lts

# root 권한으로 전환
USER root

# 필수 패키지 설치
RUN apt-get update && apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/*

# Docker CLI 설치
RUN curl -fsSL https://get.docker.com -o get-docker.sh && \
    sh get-docker.sh && \
    rm get-docker.sh

# Docker Compose 설치
RUN curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose && \
    chmod +x /usr/local/bin/docker-compose

# kubectl 설치
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# jenkins 유저를 docker 그룹에 추가
RUN groupadd -f docker && usermod -aG docker jenkins

# jenkins 유저로 복귀
USER jenkins

# 플러그인 자동 설치
COPY plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# JCasC (Jenkins Configuration as Code) 설정
COPY jenkins.yaml /var/jenkins_home/casc_configs/jenkins.yaml
ENV CASC_JENKINS_CONFIG=/var/jenkins_home/casc_configs/jenkins.yaml

# 초기 관리자 계정 설정 스킵
ENV JAVA_OPTS="-Djenkins.install.runSetupWizard=false"
```

### plugins.txt

```text
git:latest
workflow-aggregator:latest
docker-workflow:latest
kubernetes:latest
configuration-as-code:latest
job-dsl:latest
blueocean:latest
credentials-binding:latest
github:latest
gitlab-plugin:latest
pipeline-stage-view:latest
prometheus:latest
slack:latest
email-ext:latest
locale:latest
timezone:latest
```

### jenkins.yaml (JCasC)

```yaml
jenkins:
  systemMessage: "Jenkins configured automatically by Jenkins Configuration as Code"
  numExecutors: 2
  mode: NORMAL
  scmCheckoutRetryCount: 3
  labelString: "master"
  
  securityRealm:
    local:
      allowsSignup: false
      users:
        - id: "admin"
          password: "${JENKINS_ADMIN_PASSWORD:-admin123}"
          
  authorizationStrategy:
    loggedInUsersCanDoAnything:
      allowAnonymousRead: false

  clouds:
    - docker:
        name: "docker"
        dockerApi:
          dockerHost:
            uri: "unix:///var/run/docker.sock"

  globalNodeProperties:
    - envVars:
        env:
          - key: "TZ"
            value: "Asia/Seoul"

credentials:
  system:
    domainCredentials:
      - credentials:
          - usernamePassword:
              scope: GLOBAL
              id: "github-credentials"
              username: "${GITHUB_USERNAME}"
              password: "${GITHUB_TOKEN}"
              description: "GitHub credentials"

unclassified:
  location:
    url: "http://jenkins:8080/"
    adminAddress: "admin@example.com"
  
  slackNotifier:
    teamDomain: "${SLACK_TEAM}"
    tokenCredentialId: "slack-token"
```

### docker-compose.yml (커스텀 이미지 사용)

```yaml
version: '3.8'

services:
  jenkins-custom:
    build:
      context: ./jenkins
      dockerfile: Dockerfile
    container_name: jenkins-custom
    hostname: jenkins
    restart: unless-stopped
    privileged: true
    user: root
    ports:
      - "8080:8080"
      - "50000:50000"
    environment:
      - JENKINS_ADMIN_PASSWORD=${JENKINS_ADMIN_PASSWORD:-admin123}
      - GITHUB_USERNAME=${GITHUB_USERNAME}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - SLACK_TEAM=${SLACK_TEAM}
      - JAVA_OPTS=-Xmx2g -Xms512m
      - TZ=Asia/Seoul
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - microservices
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/login"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 90s

volumes:
  jenkins_home:

networks:
  microservices:
    external: true
```

## Jenkins + SonarQube + Nexus (통합 CI/CD)

```yaml
version: '3.8'

services:
  jenkins:
    image: jenkins/jenkins:lts
    container_name: jenkins
    restart: unless-stopped
    privileged: true
    user: root
    ports:
      - "8080:8080"
      - "50000:50000"
    environment:
      - JAVA_OPTS=-Xmx2g
      - TZ=Asia/Seoul
    volumes:
      - jenkins_home:/var/jenkins_home
      - /var/run/docker.sock:/var/run/docker.sock
    networks:
      - microservices
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/login"]
      interval: 30s
      timeout: 10s
      retries: 5

  sonarqube:
    image: sonarqube:lts-community
    container_name: sonarqube
    restart: unless-stopped
    ports:
      - "9000:9000"
    environment:
      - SONAR_JDBC_URL=jdbc:postgresql://sonarqube-db:5432/sonar
      - SONAR_JDBC_USERNAME=sonar
      - SONAR_JDBC_PASSWORD=sonar
    volumes:
      - sonarqube_data:/opt/sonarqube/data
      - sonarqube_extensions:/opt/sonarqube/extensions
      - sonarqube_logs:/opt/sonarqube/logs
    networks:
      - microservices
    depends_on:
      - sonarqube-db

  sonarqube-db:
    image: postgres:15-alpine
    container_name: sonarqube-db
    restart: unless-stopped
    environment:
      - POSTGRES_USER=sonar
      - POSTGRES_PASSWORD=sonar
      - POSTGRES_DB=sonar
    volumes:
      - sonarqube_db:/var/lib/postgresql/data
    networks:
      - microservices

  nexus:
    image: sonatype/nexus3:latest
    container_name: nexus
    restart: unless-stopped
    ports:
      - "8081:8081"
      - "8082:8082"  # Docker registry
    environment:
      - INSTALL4J_ADD_VM_PARAMS=-Xms1g -Xmx2g -XX:MaxDirectMemorySize=2g
    volumes:
      - nexus_data:/nexus-data
    networks:
      - microservices
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/"]
      interval: 30s
      timeout: 10s
      retries: 5

volumes:
  jenkins_home:
  sonarqube_data:
  sonarqube_extensions:
  sonarqube_logs:
  sonarqube_db:
  nexus_data:

networks:
  microservices:
    external: true
```

## 백업 스크립트

```bash
#!/bin/bash
# backup-jenkins.sh

BACKUP_DIR="/backup/jenkins"
DATE=$(date +%Y%m%d_%H%M%S)
CONTAINER_NAME="jenkins"

# 백업 디렉토리 생성
mkdir -p $BACKUP_DIR

# Jenkins 데이터 백업
docker exec $CONTAINER_NAME tar czf - /var/jenkins_home \
  --exclude=/var/jenkins_home/workspace \
  --exclude=/var/jenkins_home/logs \
  > $BACKUP_DIR/jenkins_home_$DATE.tar.gz

# 7일 이상 된 백업 삭제
find $BACKUP_DIR -name "jenkins_*.tar.gz" -mtime +7 -delete

echo "Jenkins backup completed: $BACKUP_DIR/jenkins_home_$DATE.tar.gz"
```

## .env 파일 예시

```bash
# Jenkins 설정
JENKINS_ADMIN_PASSWORD=your_secure_password

# GitHub 인증
GITHUB_USERNAME=your_username
GITHUB_TOKEN=your_github_token

# Slack 알림
SLACK_TEAM=your_team

# SonarQube
SONAR_JDBC_PASSWORD=sonar_password

# Nexus
NEXUS_ADMIN_PASSWORD=nexus_password
```

## 초기 설정 스크립트

```bash
#!/bin/bash
# init-jenkins.sh

# Jenkins 초기 비밀번호 확인
echo "=== Jenkins Initial Password ==="
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword

# SonarQube 토큰 생성 대기
echo "=== Waiting for SonarQube ==="
until curl -s http://localhost:9000/api/system/status | grep -q "UP"; do
  sleep 5
done

# Nexus 관리자 비밀번호
echo "=== Nexus Admin Password ==="
docker exec nexus cat /nexus-data/admin.password

echo "=== Setup Complete ==="
echo "Jenkins: http://localhost:8080"
echo "SonarQube: http://localhost:9000"
echo "Nexus: http://localhost:8081"
```

## 사용 방법

1. **네트워크 생성**:
```bash
docker network create microservices
```

2. **환경 변수 설정**:
```bash
cp .env.example .env
```

3. **Jenkins 시작**:
```bash
docker-compose up -d jenkins
```

4. **초기 비밀번호 확인**:
```bash
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

5. **접속**: http://localhost:8080
