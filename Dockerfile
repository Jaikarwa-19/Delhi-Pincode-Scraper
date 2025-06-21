# ✅ Use official Playwright image with all browsers and OS libs preinstalled
FROM mcr.microsoft.com/playwright/python:v1.44.0-focal

# Create app directory
WORKDIR /app

# Copy all local files into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 🧠 Optional: This installs browser binaries (usually already in base image)
RUN playwright install

# Define environment variable placeholder (set value in Render UI)
ENV GOOGLE_MAPS_API_KEY=""

# Run your script
CMD ["python", "main.py"]
