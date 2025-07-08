# Use official Python 3.11 image
FROM python:3.11-slim

# Install Chromium and its driver
RUN apt-get update && \
    apt-get install -y chromium chromium-driver && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the app with Gunicorn (fixed PORT handling)
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT --timeout 180 --workers 1 --threads 1 --worker-class sync app:app"]