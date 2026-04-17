# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory to the root of the repo
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from the root requirements file
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Run collectstatic for Django
# Note: SECRET_KEY and DATABASE_URL are not strictly needed for basic collectstatic 
# but if settings fail without them, we provide a placeholder
RUN DATABASE_URL=postgres://dummy SECRET_KEY=dummy python backend/manage.py collectstatic --noinput

# The service will run from the root, but we point to the backend's wsgi
# Use --chdir to navigate into the backend directory where manage.py and wsgi are
CMD ["gunicorn", "--chdir", "backend", "counselling_platform.wsgi:application", "--bind", "0.0.0.0:10000"]
