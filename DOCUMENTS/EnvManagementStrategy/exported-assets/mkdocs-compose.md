# MkDocs 자동 빌드 및 배포 Docker Compose

## 자동 빌드 및 Serve (개발 모드)

```yaml
version: '3.8'

services:
  mkdocs:
    image: squidfunk/mkdocs-material:latest
    container_name: mkdocs-dev
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      - ./docs:/docs
      - ./mkdocs.yml:/docs/mkdocs.yml:ro
    environment:
      # 실시간 리로드 활성화
      LIVE_RELOAD_SUPPORT: 'true'
      FAST_MODE: 'true'
    command: serve --dev-addr=0.0.0.0:8000
    networks:
      - microservices

networks:
  microservices:
    external: true
```

## Git 저장소 자동 동기화 + 빌드 + 배포

```yaml
version: '3.8'

services:
  mkdocs-auto-build:
    image: polinux/mkdocs:latest
    container_name: mkdocs-auto-build
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      # 실시간 리로드
      LIVE_RELOAD_SUPPORT: 'true'
      
      # 추가 플러그인 설치
      ADD_MODULES: 'mkdocs-material mkdocs-git-revision-date-localized-plugin pymdown-extensions'
      
      # 빠른 빌드 모드 (변경된 파일만)
      FAST_MODE: 'true'
      
      # 문서 디렉토리
      DOCS_DIRECTORY: '/docs'
      
      # Git 저장소 (선택사항)
      GIT_REPO: 'https://github.com/username/docs.git'
      GIT_BRANCH: 'main'
      
      # 자동 업데이트
      AUTO_UPDATE: 'true'
      UPDATE_INTERVAL: 5  # 5분마다 git pull
      
      # 서버 주소
      DEV_ADDR: '0.0.0.0:8000'
    volumes:
      # 로컬 문서 마운트 (Git 사용 안 할 경우)
      - ./docs:/docs
      # SSH 키 (Private 저장소 사용시)
      # - ~/.ssh/id_rsa:/root/.ssh/id_rsa:ro
    networks:
      - microservices
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  microservices:
    external: true
```

## 프로덕션 빌드 + Nginx 배포

```yaml
version: '3.8'

services:
  mkdocs-builder:
    image: squidfunk/mkdocs-material:latest
    container_name: mkdocs-builder
    volumes:
      - ./docs:/docs
      - ./site:/docs/site
    command: build --clean --strict
    networks:
      - microservices

  mkdocs-nginx:
    image: nginx:alpine
    container_name: mkdocs-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./site:/usr/share/nginx/html:ro
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    networks:
      - microservices
    depends_on:
      - mkdocs-builder
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  microservices:
    external: true
```

## CI/CD 통합 자동 빌드 파이프라인

```yaml
version: '3.8'

services:
  # Git 저장소 동기화 서비스
  docs-sync:
    image: alpine/git:latest
    container_name: docs-sync
    restart: unless-stopped
    volumes:
      - docs_repo:/repo
    entrypoint: /bin/sh
    command: |
      -c "
      if [ ! -d /repo/.git ]; then
        git clone ${GIT_REPO:-https://github.com/username/docs.git} /repo
      fi
      while true; do
        cd /repo
        git pull origin ${GIT_BRANCH:-main}
        sleep ${UPDATE_INTERVAL:-300}
      done
      "
    environment:
      GIT_REPO: 'https://github.com/username/docs.git'
      GIT_BRANCH: 'main'
      UPDATE_INTERVAL: '300'  # 5분
    networks:
      - microservices

  # MkDocs 빌드 감시 및 자동 재빌드
  mkdocs-watch:
    image: squidfunk/mkdocs-material:latest
    container_name: mkdocs-watch
    restart: unless-stopped
    volumes:
      - docs_repo:/docs:ro
      - mkdocs_site:/site
    command: sh -c "mkdocs build -d /site && while true; do sleep 300; mkdocs build -d /site; done"
    networks:
      - microservices
    depends_on:
      - docs-sync

  # Nginx 웹 서버
  mkdocs-server:
    image: nginx:alpine
    container_name: mkdocs-server
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - mkdocs_site:/usr/share/nginx/html:ro
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
    networks:
      - microservices
    depends_on:
      - mkdocs-watch
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  docs_repo:
  mkdocs_site:

networks:
  microservices:
    external: true
```

## 커스텀 MkDocs Dockerfile (플러그인 포함)

```dockerfile
FROM python:3.11-alpine

WORKDIR /docs

# 빌드 의존성 설치
RUN apk add --no-cache \
    git \
    git-fast-import \
    openssh-client \
    curl \
    && pip install --no-cache-dir \
    mkdocs-material \
    mkdocs-git-revision-date-localized-plugin \
    mkdocs-minify-plugin \
    mkdocs-redirects \
    pymdown-extensions \
    pillow \
    cairosvg

# 비root 유저
RUN addgroup -g 1000 mkdocs && \
    adduser -u 1000 -G mkdocs -s /bin/sh -D mkdocs

USER mkdocs

EXPOSE 8000

# 개발 서버 실행
CMD ["mkdocs", "serve", "--dev-addr=0.0.0.0:8000"]
```

## mkdocs.yml 설정 예시

```yaml
site_name: 프로젝트 문서
site_url: https://docs.example.com
repo_url: https://github.com/username/project
repo_name: username/project

theme:
  name: material
  language: ko
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.top
    - search.suggest
    - search.highlight
    - content.code.copy
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: 다크 모드로 전환
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: 라이트 모드로 전환

plugins:
  - search:
      lang: ko
  - git-revision-date-localized:
      enable_creation_date: true
  - minify:
      minify_html: true

markdown_extensions:
  - pymdownx.highlight
  - pymdownx.superfences
  - pymdownx.tabbed
  - admonition
  - codehilite

nav:
  - 홈: index.md
  - 시작하기: getting-started.md
  - API 문서: api/
```

## Nginx 설정 (./nginx/default.conf)

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip 압축
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # 캐시 설정
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # HTML 파일
    location / {
        try_files $uri $uri/ $uri.html =404;
    }

    # 404 페이지
    error_page 404 /404.html;
}
```

## docker-compose 명령어

```bash
# 개발 서버 시작 (실시간 리로드)
docker-compose up mkdocs

# 프로덕션 빌드 및 배포
docker-compose up mkdocs-builder mkdocs-nginx

# Git 자동 동기화 + 빌드
docker-compose up docs-sync mkdocs-watch mkdocs-server

# 전체 스택 시작
docker-compose up -d

# 수동으로 빌드 트리거
docker-compose exec mkdocs-watch mkdocs build -d /site

# 로그 확인
docker-compose logs -f mkdocs-watch
```

## 사용 시나리오

### 시나리오 1: 로컬 개발
- `mkdocs` 서비스 사용
- 파일 변경시 자동 리로드

### 시나리오 2: Git 저장소 연동
- `mkdocs-auto-build` 서비스 사용
- 5분마다 자동 git pull 및 재빌드

### 시나리오 3: 프로덕션 배포
- `mkdocs-builder` + `mkdocs-nginx` 사용
- 정적 사이트 생성 후 Nginx로 서빙
