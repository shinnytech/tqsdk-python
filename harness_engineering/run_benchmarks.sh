#!/bin/bash
# Benchmark each commit ahead of origin/master
# Runs backtest.py for each commit and saves output to a log file

set -e

REPO_DIR="/home/zzk/Projects/tqsdk-python"
TEST_DIR="/home/zzk/Projects/tq_sdk_test"
CURRENT_BRANCH=$(git -C "$REPO_DIR" rev-parse --abbrev-ref HEAD)

# Get commits in chronological order (oldest first)
mapfile -t COMMITS < <(git -C "$REPO_DIR" log --reverse --format="%H %s" origin/master..HEAD)

TOTAL=${#COMMITS[@]}
echo "Found $TOTAL commits to benchmark"
echo "Current branch: $CURRENT_BRANCH"
echo ""

COUNT=0
for entry in "${COMMITS[@]}"; do
    HASH="${entry%% *}"
    MESSAGE="${entry#* }"
    SHORT_HASH="${HASH:0:7}"
    COUNT=$((COUNT + 1))

    # Sanitize message: first 50 chars, replace non-alphanumeric with _
    SAFE_MSG=$(echo "$MESSAGE" | head -c 50 | sed 's/[^a-zA-Z0-9_-]/_/g')
    LOGFILE="${TEST_DIR}/${COUNT}_${SAFE_MSG}_${SHORT_HASH}.log"

    echo "[$COUNT/$TOTAL] $SHORT_HASH $MESSAGE"

    # Checkout the commit
    git -C "$REPO_DIR" checkout --quiet "$HASH"

    # Run backtest and save output
    echo "Commit: $SHORT_HASH $MESSAGE" > "$LOGFILE"
    echo "Date: $(git -C "$REPO_DIR" log -1 --format='%ci' "$HASH")" >> "$LOGFILE"
    echo "---" >> "$LOGFILE"
    (cd "$TEST_DIR" && uv run backtest.py) >> "$LOGFILE" 2>&1 || true

    echo "  -> saved to $(basename "$LOGFILE")"
    echo ""
done

# Restore original branch
echo "Restoring branch: $CURRENT_BRANCH"
git -C "$REPO_DIR" checkout --quiet "$CURRENT_BRANCH"
echo "Done! All $TOTAL benchmarks complete."
