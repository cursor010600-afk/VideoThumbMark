# Use official Python image with newer version
FROM python:3.11-slim

# Install FFmpeg, fonts, and cleanup in single layer to reduce image size
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    echo "Verifying font installation..." && \
    ls -la /usr/share/fonts/truetype/dejavu/ || echo "DejaVu fonts not found!"

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for temporary files in /tmp (cloud storage)
RUN mkdir -p /tmp/Watermarked /tmp/Thumbnails /tmp/Metadata /tmp/Renames

# Command to run the bot
CMD echo "Starting bot..." && \
    echo "Checking fonts..." && \
    ls -la /usr/share/fonts/truetype/dejavu/ 2>/dev/null || echo "Warning: DejaVu fonts not found" && \
    python bot.py

