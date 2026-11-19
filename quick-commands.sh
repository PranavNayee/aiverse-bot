#!/bin/bash
# AIVerse Bot - Quick Command Reference
# Make executable: chmod +x quick-commands.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 AIVerse Bot - Quick Commands${NC}\n"

show_menu() {
    echo -e "${GREEN}=== Status & Monitoring ===${NC}"
    echo "1)  Check workflow status"
    echo "2)  View recent runs"
    echo "3)  Watch live run"
    echo "4)  View latest logs"
    echo ""
    echo -e "${GREEN}=== Manual Triggers ===${NC}"
    echo "5)  Make & post reel NOW"
    echo "6)  Test run (dry run)"
    echo "7)  Force post queued reel"
    echo "8)  Weekly report now"
    echo "9)  Run pre-flight check"
    echo ""
    echo -e "${GREEN}=== Content Creation ===${NC}"
    echo "10) Make lesson reel"
    echo "11) Make trick reel"
    echo "12) Make news reel"
    echo "13) Test with YouTube preview"
    echo ""
    echo -e "${GREEN}=== Management ===${NC}"
    echo "14) List secrets"
    echo "15) List variables"
    echo "16) Update Instagram token"
    echo "17) View configuration"
    echo ""
    echo -e "${GREEN}=== Testing ===${NC}"
    echo "18) Test voice samples"
    echo "19) Test AI image generation"
    echo "20) Run offline test"
    echo ""
    echo "0)  Exit"
    echo ""
}

# Status commands
check_status() {
    echo -e "${BLUE}📊 Checking workflow status...${NC}"
    gh workflow list
}

view_runs() {
    echo -e "${BLUE}📋 Recent workflow runs:${NC}"
    gh run list --limit 10
}

watch_run() {
    echo -e "${BLUE}👀 Watching live run...${NC}"
    gh run watch
}

view_logs() {
    echo -e "${BLUE}📄 Latest run logs:${NC}"
    gh run view --log
}

# Trigger commands
post_now() {
    echo -e "${YELLOW}⚡ Making and posting reel immediately...${NC}"
    gh workflow run daily.yml --field post_now=true
    echo -e "${GREEN}✅ Triggered! Check status with option 2${NC}"
}

dry_run() {
    echo -e "${YELLOW}🧪 Running test (Telegram preview only)...${NC}"
    gh workflow run daily.yml --field dry_run=true --field content=lesson
    echo -e "${GREEN}✅ Triggered! Check Telegram for preview${NC}"
}

force_post() {
    echo -e "${YELLOW}🚀 Force posting queued reel...${NC}"
    gh workflow run post.yml --field force_post=true
    echo -e "${GREEN}✅ Triggered! Reel will post soon${NC}"
}

weekly_report() {
    echo -e "${YELLOW}📊 Generating weekly report...${NC}"
    gh workflow run engage.yml --field force_report=true
    echo -e "${GREEN}✅ Triggered! Check Telegram for report${NC}"
}

preflight() {
    echo -e "${YELLOW}🔍 Running pre-flight check...${NC}"
    gh workflow run check.yml
    echo -e "${GREEN}✅ Triggered! Check status with option 2${NC}"
}

# Content commands
make_lesson() {
    echo -e "${YELLOW}📚 Making lesson reel...${NC}"
    gh workflow run daily.yml --field content=lesson --field dry_run=true
    echo -e "${GREEN}✅ Triggered! Check Telegram for preview${NC}"
}

make_trick() {
    echo -e "${YELLOW}💡 Making trick reel...${NC}"
    gh workflow run daily.yml --field content=trick --field dry_run=true
    echo -e "${GREEN}✅ Triggered! Check Telegram for preview${NC}"
}

make_news() {
    echo -e "${YELLOW}📰 Making news reel...${NC}"
    gh workflow run daily.yml --field content=news --field dry_run=true
    echo -e "${GREEN}✅ Triggered! Check Telegram for preview${NC}"
}

youtube_preview() {
    echo -e "${YELLOW}🎬 Making reel with YouTube preview...${NC}"
    gh workflow run daily.yml --field dry_run=true --field youtube_preview=true
    echo -e "${GREEN}✅ Triggered! Will upload to YouTube as private${NC}"
}

# Management commands
list_secrets() {
    echo -e "${BLUE}🔐 Configured secrets:${NC}"
    gh secret list
}

list_variables() {
    echo -e "${BLUE}⚙️  Configured variables:${NC}"
    gh variable list
}

update_token() {
    echo -e "${YELLOW}🔑 Update Instagram Access Token${NC}"
    echo "Enter new token (or press Ctrl+C to cancel):"
    read -s token
    if [ -n "$token" ]; then
        echo "$token" | gh secret set IG_ACCESS_TOKEN
        echo -e "${GREEN}✅ Token updated successfully!${NC}"
    else
        echo -e "${RED}❌ No token provided${NC}"
    fi
}

view_config() {
    echo -e "${BLUE}⚙️  Current Configuration:${NC}\n"
    echo "=== Secrets ==="
    gh secret list
    echo ""
    echo "=== Variables ==="
    gh variable list
    echo ""
    echo "=== Workflows ==="
    gh workflow list
}

# Testing commands
test_voices() {
    echo -e "${YELLOW}🎤 Testing all voice samples...${NC}"
    gh workflow run check.yml --field voice_samples=true
    echo -e "${GREEN}✅ Triggered! Check artifacts when complete${NC}"
}

test_image() {
    echo -e "${YELLOW}🎨 Testing AI image generation...${NC}"
    gh workflow run check.yml --field image_test=true
    echo -e "${GREEN}✅ Triggered! Check artifacts when complete${NC}"
}

offline_test() {
    echo -e "${YELLOW}🧪 Running offline test...${NC}"
    cd cartoon-bot
    python tests/offline_test.py
    cd ..
    echo -e "${GREEN}✅ Offline test complete!${NC}"
}

# Main loop
while true; do
    show_menu
    read -p "Enter choice [0-20]: " choice
    echo ""
    
    case $choice in
        1) check_status ;;
        2) view_runs ;;
        3) watch_run ;;
        4) view_logs ;;
        5) post_now ;;
        6) dry_run ;;
        7) force_post ;;
        8) weekly_report ;;
        9) preflight ;;
        10) make_lesson ;;
        11) make_trick ;;
        12) make_news ;;
        13) youtube_preview ;;
        14) list_secrets ;;
        15) list_variables ;;
        16) update_token ;;
        17) view_config ;;
        18) test_voices ;;
        19) test_image ;;
        20) offline_test ;;
        0) 
            echo -e "${GREEN}👋 Happy automating!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Invalid option${NC}"
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
    clear
done
