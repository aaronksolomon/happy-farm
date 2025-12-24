#!/bin/bash
# Quick test to extract HTML sections and test tnh-fab manually

set -e

URL="https://www.johnnyseeds.com/vegetables/broccoli/standard-broccoli/belstar-organic-f1-broccoli-seed-2815G.html"
CACHE_DIR="/tmp/happy-farm-scraper"
PROMPT_FILE="$HOME/Desktop/Projects/happy-farm/prompts/extract_johnnys_seeds_data.md"

echo "Downloading Johnny's Seeds page..."
mkdir -p "$CACHE_DIR"
curl -s -A "HappyFarmBot/1.0 (educational research)" "$URL" > "$CACHE_DIR/test_page.html"

echo "✓ Downloaded to $CACHE_DIR/test_page.html"
echo ""
echo "Now test manually with:"
echo "cd ~/Desktop/Projects/tnh-scholar"
echo "tnh-fab run $PROMPT_FILE $CACHE_DIR/test_page.html"
