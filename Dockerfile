# Use official Python 3.11 image (3.13 may have compatibility issues)
FROM python:3.11-slim

# Install Chromium and its driver (essential for Selenium)
RUN apt-get update && \
    apt-get install -y chromium chromium-driver && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all files (except those in .dockerignore)
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "--timeout", "180", "--workers", "1", "--threads", "1", "--worker-class", "sync", "app:app"]