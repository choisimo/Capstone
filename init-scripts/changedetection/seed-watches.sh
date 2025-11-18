#!/bin/sh

CHD_ADDR="${CHANGEDETECTION_BASE_URL:-http://changedetection:5000}"
API_KEY="${CHANGEDETECTION_API_KEY:-}"

echo "[changedetection-seed] Using changedetection base URL: $CHD_ADDR"

# Wait for changedetection to be ready and initialize
echo "[changedetection-seed] Waiting for changedetection to initialize..."
for i in $(seq 1 60); do
  if curl -s "$CHD_ADDR" >/dev/null 2>&1; then
    echo "[changedetection-seed] changedetection is responding"
    sleep 3  # Give it a bit more time to create the datastore
    break
  fi
  echo "[changedetection-seed] Waiting for changedetection to be ready... ($i/60)"
  sleep 2
done

# If API_KEY is not provided, try to extract it from changedetection's datastore
if [ -z "$API_KEY" ]; then
  echo "[changedetection-seed] API key not provided, attempting to extract from datastore..."
  
  if [ -f /datastore/url-watches.json ]; then
    API_KEY=$(grep -o '"api_access_token": "[^"]*"' /datastore/url-watches.json | head -1 | cut -d'"' -f4)
    
    if [ -n "$API_KEY" ]; then
      echo "[changedetection-seed] Successfully extracted API key from datastore"
    else
      echo "[changedetection-seed] Failed to extract API key from datastore"
      echo "[changedetection-seed] Please set CHANGEDETECTION_API_KEY environment variable"
      exit 0
    fi
  else
    echo "[changedetection-seed] Datastore file not found at /datastore/url-watches.json"
    echo "[changedetection-seed] Please set CHANGEDETECTION_API_KEY environment variable"
    exit 0
  fi
else
  echo "[changedetection-seed] Using provided API key"
fi

# Check if watch already exists
watch_exists() {
  URL="$1"
  WATCHES=$(curl -s "$CHD_ADDR/api/v1/watch" -H "x-api-key: $API_KEY")
  echo "$WATCHES" | grep -q "\"url\": \"$URL\""
  return $?
}

import_watch() {
  URL="$1"
  TITLE="$2"
  
  if watch_exists "$URL"; then
    echo "[changedetection-seed] Watch already exists: $TITLE ($URL)"
    return 0
  fi
  
  echo "[changedetection-seed] Adding watch: $TITLE ($URL)"
  RESPONSE=$(curl -s -X POST "$CHD_ADDR/api/v1/watch" \
    -H "x-api-key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"url\": \"$URL\", \"title\": \"$TITLE\"}")
  
  if echo "$RESPONSE" | grep -q "uuid"; then
    echo "[changedetection-seed] Successfully added: $TITLE"
  else
    echo "[changedetection-seed] Failed to add: $TITLE - $RESPONSE"
  fi
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

seed_watches() {
  WATCH_DATA="$1"

  while IFS='|' read -r URL TITLE; do
    [ -z "$URL" ] && continue
    import_watch "$URL" "$TITLE"
    sleep 0.3
  done <<EOF
$WATCH_DATA
EOF
}

echo "[changedetection-seed] Seeding news watches..."
seed_watches "$NEWS_WATCHES"

echo "[changedetection-seed] Seeding community watches..."
seed_watches "$COMMUNITY_WATCHES"

echo "[changedetection-seed] Seed completed."
exit 0
