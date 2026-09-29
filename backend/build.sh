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
