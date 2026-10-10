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
pip install -r "$BACKEND_DIR/requirements.txt"

# Run migrations FIRST
python "$BACKEND_DIR/manage.py" migrate

# Verify migrations and system
echo "🔍 Running system verification..."
python "$BACKEND_DIR/verify_and_fix.py" || true

# Auto-fix owner account (ALWAYS ensures owner can login)
echo "🔧 Running auto_fix_owner.py..."
python "$BACKEND_DIR/auto_fix_owner.py"

# Convert static files
python "$BACKEND_DIR/manage.py" collectstatic --noinput
