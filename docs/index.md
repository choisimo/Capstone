# Capstone Project WIKI

Capstone 프로젝트의 모든 문서를 한 곳에서 확인할 수 있는 중앙 허브입니다.

## 시작하기

1. 좌측 네비게이션에서 문서를 선택하거나, 상단 검색을 통해 문서를 빠르게 찾아보세요.
2. 문서 구조는 `python scripts/generate_wiki_manifest.py --format yaml` 명령으로 자동 생성할 수 있습니다.

## 문서 갱신 방법

```bash
# JSON manifest 갱신 (docs/wiki/data/docs.json)
python scripts/generate_wiki_manifest.py

# MkDocs 네비게이션 YAML 출력 (콘솔)
python scripts/generate_wiki_manifest.py --format yaml

# MkDocs 개발 서버 실행
mkdocs serve
```

필요 시 GitHub Pages 또는 별도 호스팅 환경에 MkDocs 빌드 결과를 배포하여 팀 구성원과 공유할 수 있습니다.
