#!/usr/bin/env bash
# build.sh — works whether Root Directory is repo root OR backend/
set -o errexit

# Detect if we're inside backend/ or at repo root
if [ -f "manage.py" ]; then
    # We're inside backend/
    REPO_ROOT=".."
    BACKEND_DIR="."
elif [ -f "backend/manage.py" ]; then
    # We're at repo root
    REPO_ROOT="."
    BACKEND_DIR="backend"
else
    echo "❌ Cannot find manage.py. Check your Root Directory setting."
    exit 1
fi

# Install dependencies
pip install -r "$REPO_ROOT/requirements.txt"

# Convert static files
python "$BACKEND_DIR/manage.py" collectstatic --noinput

# Run migrations
python "$BACKEND_DIR/manage.py" migrate

# Auto-fix owner account (ALWAYS ensures owner can login)
python "$BACKEND_DIR/auto_fix_owner.py"
