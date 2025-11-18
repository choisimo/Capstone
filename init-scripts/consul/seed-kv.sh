#!/bin/sh

echo "[consul-kv-init] Seeding Consul KV..."

# Default Consul address if not provided
ADDR="${CONSUL_HTTP_ADDR:-http://consul:8500}"

echo "[consul-kv-init] CONSUL_HTTP_ADDR=${ADDR}"

# Seed Perplexity API key
if [ -n "${PERPLEXITY_API_KEY}" ]; then
  echo "[consul-kv-init] Setting Perplexity API key..."
  curl -s -X PUT \
    -H "X-Consul-Token: ${CONSUL_HTTP_TOKEN}" \
    --data "${PERPLEXITY_API_KEY}" \
    "${ADDR}/v1/kv/config/analysis/dev/secrets/perplexity/api_key" \
    || echo "[consul-kv-init] Failed to set Perplexity API key"
else
  echo "[consul-kv-init] PERPLEXITY_API_KEY is empty, skip"
fi

# Seed changedetection API key
if [ -n "${CHANGEDETECTION_API_KEY}" ]; then
  echo "[consul-kv-init] Setting changedetection API key..."
  curl -s -X PUT \
    -H "X-Consul-Token: ${CONSUL_HTTP_TOKEN}" \
    --data "${CHANGEDETECTION_API_KEY}" \
    "${ADDR}/v1/kv/config/analysis/dev/secrets/changedetection/api_key" \
    || echo "[consul-kv-init] Failed to set changedetection API key"
else
  echo "[consul-kv-init] CHANGEDETECTION_API_KEY is empty, skip"
fi

echo "[consul-kv-init] Done."
exit 0
