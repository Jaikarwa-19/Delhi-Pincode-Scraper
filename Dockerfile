# Use a Playwright base image with all browser dependencies
FROM mcr.microsoft.com/playwright/python:v1.43.1-jammy

# Set working directory inside container
WORKDIR /app

# Copy project files into container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser binaries (redundant but safe)
RUN playwright install

# The API key is injected securely via Render's environment UI
# No need to hardcode it here

# Run the main script
CMD ["python", "main.py"]
