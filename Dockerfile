# Use a lightweight Python base image
FROM python:3.11-slim

# Install system dependencies (FFmpeg is required by yt-dlp)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Set working directory inside container
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project files
COPY . .

# Expose port (Render expects this)
EXPOSE 10000
ENV PORT=10000
ENV PYTHONUNBUFFERED=1

# Start the app with Gunicorn (production server)
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:10000", "app:app"]
