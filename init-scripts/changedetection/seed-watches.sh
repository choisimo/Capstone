#!/bin/sh

CHD_ADDR="${CHANGEDETECTION_BASE_URL:-http://changedetection:5000}"
API_KEY="${CHANGEDETECTION_API_KEY:-}"

# Install jq once (curlimages/curl is Alpine-based)
if ! command -v jq >/dev/null 2>&1; then
  apk add --no-cache jq >/dev/null
fi

if [ -z "$API_KEY" ]; then
  echo "[changedetection-seed] CHANGEDETECTION_API_KEY is empty. Skipping seed."
  exit 0
fi

echo "[changedetection-seed] Using changedetection base URL: $CHD_ADDR"

ensure_tag() {
  TAG_NAME="$1"
  echo "[changedetection-seed] Ensuring tag exists: $TAG_NAME"

  CREATE_RESP=$(curl -s -X POST "$CHD_ADDR/api/v1/tag" \
    -H "x-api-key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"tag\": \"$TAG_NAME\"}")

  TAG_UUID=$(echo "$CREATE_RESP" | jq -r '.uuid // empty')

  if [ -z "$TAG_UUID" ] || [ "$TAG_UUID" = "null" ]; then
    LIST_RESP=$(curl -s "$CHD_ADDR/api/v1/tag" -H "x-api-key: $API_KEY")
    TAG_UUID=$(echo "$LIST_RESP" | jq -r ".tags[] | select(.title == \"$TAG_NAME\").uuid" | head -n 1)
  fi

  if [ -z "$TAG_UUID" ] || [ "$TAG_UUID" = "null" ]; then
    echo "[changedetection-seed] Failed to resolve tag $TAG_NAME"
    return 1
  fi

  echo "$TAG_UUID"
}

# shellcheck disable=SC2120
import_watch() {
  URL="$1"
  TITLE="$2"
  TAG_UUID="$3"
  echo "[changedetection-seed] Adding watch: $TITLE ($URL)"
  curl -s -X POST "$CHD_ADDR/api/v1/watch" \
    -H "x-api-key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"url\": \"$URL\", \"title\": \"$TITLE\", \"tags\": [\"$TAG_UUID\"], \"time_between_check\": \"7200\"}"
}

NEWS_WATCHES='
https://news.naver.com|Naver News
https://news.daum.net|Daum News
https://www.yna.co.kr|Yonhap News
https://www.news1.kr|News1
https://www.newsis.com|Newsis
https://www.nocutnews.co.kr|Nocut News
https://news.kbs.co.kr|KBS News
https://imnews.imbc.com|MBC News
https://news.sbs.co.kr|SBS News
https://news.jtbc.co.kr|JTBC News
https://www.ytn.co.kr|YTN
https://www.chosun.com|Chosun
https://www.joongang.co.kr|Joongang
https://www.donga.com|Donga
https://www.hani.co.kr|Hankyoreh
https://www.khan.co.kr|Kyunghyang
https://www.ohmynews.com|Ohmynews
https://www.mk.co.kr|Maeil
https://www.hankyung.com|Hankyung
'
COMMUNITY_WATCHES='
https://www.dcinside.com|DCInside
https://www.fmkorea.com|FM Korea
https://www.ruliweb.com|Ruliweb
https://www.pomppu.co.kr|Ppomppu
https://theqoo.net|Theqoo
https://www.instiz.net|Instiz
https://mlbpark.donga.com|MLB Park
https://www.clien.net|Clien
https://pann.nate.com|Nate Pann
https://www.todayhumor.co.kr|TodayHumor
https://www.slrclub.com|SLRClub
https://www.inven.co.kr|Inven
https://www.dogdrip.net|Dogdrip
https://www.etoland.co.kr|Etoland
https://www.bobaedream.co.kr|Bobaedream
https://www.teamblind.com/kr|Blind
'

seed_group() {
  TAG_NAME="$1"
  WATCH_DATA="$2"

  TAG_UUID=$(ensure_tag "$TAG_NAME") || return 1
  echo "[changedetection-seed] Using tag $TAG_NAME ($TAG_UUID)"

  while IFS='|' read -r URL TITLE; do
    [ -z "$URL" ] && continue
    import_watch "$URL" "$TITLE" "$TAG_UUID"
    sleep 0.5
    echo
  done <<EOF
$WATCH_DATA
EOF
}

seed_group "news" "$NEWS_WATCHES"
seed_group "community" "$COMMUNITY_WATCHES"

echo "[changedetection-seed] Seed completed."
exit 0
