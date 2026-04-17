#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Convert static files
# We run this from the root but manage.py is in backend/
python backend/manage.py collectstatic --noinput

# Run migrations
# Note: DATABASE_URL must be set in Render environment
python backend/manage.py migrate
