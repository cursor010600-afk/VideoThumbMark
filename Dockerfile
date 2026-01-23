# Use official Python image with newer version
FROM python:3.11-slim

# Install FFmpeg and cleanup in single layer to reduce image size
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for temporary files
RUN mkdir -p Watermarked Thumbnails Metadata Renames

# Command to run the bot
CMD ["python", "bot.py"]

