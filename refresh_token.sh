#!/bin/bash
# Instagram access token refresh (exchanges a token for a 60-day long-lived one).
# NEVER put real secrets in this file - the repo is public. Pass them as environment variables:
#   FB_APP_ID=... FB_APP_SECRET=... OLD_TOKEN=... ./refresh_token.sh
set -euo pipefail

: "${FB_APP_ID:?set FB_APP_ID (Meta app id)}"
: "${FB_APP_SECRET:?set FB_APP_SECRET (Meta app secret)}"
: "${OLD_TOKEN:?set OLD_TOKEN (current Instagram/Facebook user token)}"

echo "🔄 Refreshing Instagram Access Token..."
RESPONSE=$(curl -s -G "https://graph.facebook.com/v21.0/oauth/access_token" \
  --data-urlencode "grant_type=fb_exchange_token" \
  --data-urlencode "client_id=${FB_APP_ID}" \
  --data-urlencode "client_secret=${FB_APP_SECRET}" \
  --data-urlencode "fb_exchange_token=${OLD_TOKEN}")

NEW_TOKEN=$(echo "$RESPONSE" | jq -r '.access_token // empty' 2>/dev/null || true)

if [ -n "$NEW_TOKEN" ]; then
    echo "✅ New token generated. Saving it straight into the GitHub secret (not printed)..."
    if command -v gh >/dev/null; then
        printf '%s' "$NEW_TOKEN" | gh secret set IG_ACCESS_TOKEN
        echo "✅ IG_ACCESS_TOKEN updated."
    else
        echo "gh CLI not found. Run:  gh secret set IG_ACCESS_TOKEN   and paste the token from:"
        echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
    fi
else
    echo "❌ Token refresh failed:"
    echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
    echo "Generate a new token in Graph API Explorer (see GET_NEW_TOKEN.md)."
    exit 1
fi
