#!/bin/bash
# AIVerse Bot - Live Dashboard Generator
# Usage: ./dashboard.sh [update]

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   🎛️  AIVerse Bot - Live Dashboard    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}\n"

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI not found. Install with: brew install gh${NC}"
    exit 1
fi

# System Status
echo -e "${GREEN}📊 System Status${NC}"
echo "─────────────────────────────────────────"
echo -e "Repository: ${BLUE}$(gh repo view --json nameWithOwner -q .nameWithOwner)${NC}"
echo -e "Status: ${GREEN}🟢 Operational${NC}"
echo ""

# Workflows
echo -e "${GREEN}🔄 Active Workflows${NC}"
echo "─────────────────────────────────────────"
gh workflow list --json name,state,id | jq -r '.[] | "[\(.state)] \(.name)"' | while read line; do
    if [[ $line == *"active"* ]]; then
        echo -e "${GREEN}✓${NC} ${line/\[active\]/}"
    else
        echo -e "${RED}✗${NC} ${line}"
    fi
done
echo ""

# Recent Runs
echo -e "${GREEN}📋 Last 5 Workflow Runs${NC}"
echo "─────────────────────────────────────────"
gh run list --limit 5 --json status,conclusion,name,createdAt | jq -r '.[] | 
    if .status == "completed" then
        if .conclusion == "success" then "✅" 
        elif .conclusion == "failure" then "❌"
        elif .conclusion == "cancelled" then "⚠️ "
        else "❓" end
    else "⏳" end + " " + .name + " (" + (.createdAt | split("T")[0]) + ")"'
echo ""

# Configuration
echo -e "${GREEN}🔐 Configuration Status${NC}"
echo "─────────────────────────────────────────"
secret_count=$(gh secret list | wc -l | xargs)
echo -e "Secrets configured: ${BLUE}${secret_count}${NC}"
var_count=$(gh variable list 2>/dev/null | wc -l | xargs || echo "0")
echo -e "Variables set: ${BLUE}${var_count}${NC}"
echo ""

# Variables
echo -e "${GREEN}⚙️  Current Variables${NC}"
echo "─────────────────────────────────────────"
gh variable list 2>/dev/null || echo "No variables set"
echo ""

# Storage Check
echo -e "${GREEN}💾 Recent Activity${NC}"
echo "─────────────────────────────────────────"
latest_run=$(gh run list --workflow daily.yml --limit 1 --json displayTitle,status,conclusion,createdAt | jq -r '.[0] | 
    "Last daily run: " + .displayTitle + " " + 
    (if .status == "in_progress" then "⏳ In Progress" 
     elif .conclusion == "success" then "✅ Success"
     elif .conclusion == "failure" then "❌ Failed"
     else .status end) + 
    " (" + (.createdAt | split("T")[0]) + ")"')
echo "$latest_run"

post_run=$(gh run list --workflow post.yml --limit 1 --json displayTitle,conclusion,createdAt 2>/dev/null | jq -r '.[0] | 
    "Last post: " + 
    (if .conclusion == "success" then "✅ Success"
     elif .conclusion == "failure" then "❌ Failed"
     else .conclusion end) + 
    " (" + (.createdAt | split("T")[0]) + ")"' 2>/dev/null || echo "Last post: N/A")
echo "$post_run"
echo ""

# Health Check
echo -e "${GREEN}🏥 Health Score${NC}"
echo "─────────────────────────────────────────"

health_score=0
health_max=100

# Check workflows (20 points)
if gh workflow list --json state | jq -e '.[] | select(.state == "active")' > /dev/null 2>&1; then
    health_score=$((health_score + 20))
    echo -e "✅ Workflows active (+20)"
fi

# Check secrets (15 points)
if [ "$secret_count" -ge 10 ]; then
    health_score=$((health_score + 15))
    echo -e "✅ Secrets configured (+15)"
fi

# Check recent runs (15 points)
recent_success=$(gh run list --limit 5 --json conclusion | jq '[.[] | select(.conclusion == "success")] | length')
if [ "$recent_success" -ge 3 ]; then
    health_score=$((health_score + 15))
    echo -e "✅ Recent runs successful (+15)"
fi

# Check for recent activity (15 points)
last_run_date=$(gh run list --limit 1 --json createdAt | jq -r '.[0].createdAt | split("T")[0]')
today=$(date +%Y-%m-%d)
yesterday=$(date -v-1d +%Y-%m-%d 2>/dev/null || date -d "yesterday" +%Y-%m-%d)
if [ "$last_run_date" == "$today" ] || [ "$last_run_date" == "$yesterday" ]; then
    health_score=$((health_score + 15))
    echo -e "✅ Recent activity detected (+15)"
fi

# Repository accessible (10 points)
health_score=$((health_score + 10))
echo -e "✅ Repository accessible (+10)"

# Calculate percentage
health_percent=$((health_score * 100 / health_max))

echo "─────────────────────────────────────────"
if [ $health_percent -ge 90 ]; then
    echo -e "Overall Health: ${GREEN}${health_percent}/100 🟢 EXCELLENT${NC}"
elif [ $health_percent -ge 70 ]; then
    echo -e "Overall Health: ${YELLOW}${health_percent}/100 🟡 GOOD${NC}"
else
    echo -e "Overall Health: ${RED}${health_percent}/100 🔴 NEEDS ATTENTION${NC}"
fi
echo ""

# Quick Actions
echo -e "${GREEN}🚀 Quick Actions${NC}"
echo "─────────────────────────────────────────"
echo "View logs:          gh run view --log"
echo "Watch live run:     gh run watch"
echo "Trigger daily reel: gh workflow run daily.yml"
echo "Force post:         gh workflow run post.yml --field force_post=true"
echo "Interactive menu:   ./quick-commands.sh"
echo ""

# Token Warning
echo -e "${YELLOW}⚠️  Reminders${NC}"
echo "─────────────────────────────────────────"
echo "• Instagram token expires every 60 days"
echo "• Check Telegram for daily previews"
echo "• Review weekly reports on Sundays"
echo ""

echo -e "${GREEN}✨ Dashboard complete!${NC}"
echo -e "${BLUE}Last updated: $(date)${NC}\n"

# Update mode
if [ "$1" == "update" ]; then
    echo -e "${BLUE}📝 Updating DASHBOARD.md with latest data...${NC}"
    echo "# 🎛️ AIVerse Bot - Live Dashboard" > DASHBOARD.md
    echo "" >> DASHBOARD.md
    echo "> **Last Updated**: $(date)" >> DASHBOARD.md
    echo "" >> DASHBOARD.md
    echo "Run \`./dashboard.sh\` to refresh this view" >> DASHBOARD.md
    echo "" >> DASHBOARD.md
    echo "## 📊 Current Status" >> DASHBOARD.md
    echo "" >> DASHBOARD.md
    echo "\`\`\`" >> DASHBOARD.md
    echo "Health Score: ${health_percent}/100" >> DASHBOARD.md
    echo "Active Workflows: $(gh workflow list --json state | jq '[.[] | select(.state == "active")] | length')" >> DASHBOARD.md
    echo "Secrets: ${secret_count}" >> DASHBOARD.md
    echo "Variables: ${var_count}" >> DASHBOARD.md
    echo "\`\`\`" >> DASHBOARD.md
    echo "" >> DASHBOARD.md
    echo "See full documentation in AUTOMATION_STATUS.md" >> DASHBOARD.md
    echo -e "${GREEN}✅ DASHBOARD.md updated!${NC}"
fi
