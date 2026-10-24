#!/usr/bin/env bash
# build.sh — runs from backend/ directory (Render Root Directory)
set -o errexit

# We're inside backend/, repo root is one level up
REPO_ROOT=".."

# Install dependencies
pip install -r "$REPO_ROOT/requirements.txt"

# Convert static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Ensure owner account exists (does NOT reset password)
python manage.py resetowner

# Run pre-launch purge and sequence reset if triggered
if [ -f "purge_trigger.flag" ] || [ "$PURGE_TEST_DATA" = "1" ]; then
    echo "🚨 purge_trigger.flag detected: Purging test data and resetting ID sequences for launch..."
    python manage.py purge_test_data --confirm
    rm -f "purge_trigger.flag"
fi
