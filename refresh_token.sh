#!/bin/bash
# Instagram Access Token Refresh Script

APP_ID="1445425344359379"
APP_SECRET="cac042373d9d2c94c86c0a2d6229621f"
OLD_TOKEN="EAAUim1AzK9MBSxZCYAYzfMWXZB6yrCI68pJ8OAfJ2VrwhmQixdb1CZCfpHPAMDlKCkbLplSPVU2Wh6Aaguus0h9oBeYmbhCuGiZBy1G6deTYrXzZBOHitzwvBvBuncBKOb4UOzEs0GGjFYNul7OZBIZBNYuu9SNUAkv7ONVvpioZAudZBWu7eregpWsKEaXtW6uXOZAta8hBuy7Er9ZAs9bxG79bpUrJ3gIFBg21D7rs2croTMq8TI0FdiybBIpyoRLgA4TKeUkw6QlUKarS6lewpN5drVihgZDZD"

echo "🔄 Refreshing Instagram Access Token..."
echo ""

# Try to exchange for long-lived token (60 days)
RESPONSE=$(curl -s "https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=${APP_ID}&client_secret=${APP_SECRET}&fb_exchange_token=${OLD_TOKEN}")

echo "Response:"
echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
echo ""

# Extract new token
NEW_TOKEN=$(echo "$RESPONSE" | jq -r '.access_token // empty' 2>/dev/null)

if [ -n "$NEW_TOKEN" ]; then
    echo "✅ New Token Generated!"
    echo ""
    echo "📋 Copy this token:"
    echo "$NEW_TOKEN"
    echo ""
    echo "🔧 Update GitHub Secret:"
    echo "gh secret set IG_ACCESS_TOKEN --body \"$NEW_TOKEN\""
else
    echo "❌ Token refresh failed. You need to generate a new token from Graph API Explorer."
    echo ""
    echo "📝 Follow these steps:"
    echo "1. Go to: https://developers.facebook.com/tools/explorer"
    echo "2. Select your app: cartoon"
    echo "3. Click 'Get User Access Token'"
    echo "4. Select permissions: instagram_basic, instagram_content_publish"
    echo "5. Click 'Generate Access Token'"
    echo "6. Copy the new token"
    echo "7. Run: gh secret set IG_ACCESS_TOKEN --body \"YOUR_NEW_TOKEN\""
fi
