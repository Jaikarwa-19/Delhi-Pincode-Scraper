# Use official Python image
FROM python:3.10-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget gnupg curl unzip fonts-liberation \
    libnss3 libatk-bridge2.0-0 libxss1 libasound2 \
    libgtk-3-0 libgtk-4-1 libgbm1 libxshmfence1 \
    libgraphene-1.0-0 libxrandr2 libxdamage1 libxcomposite1 \
    libx11-xcb1 libxcb1 libxext6 libxfixes3 libxrender1 \
    ca-certificates && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and its browsers
RUN python -m playwright install --with-deps

# Start the script
CMD ["python", "main.py"]
