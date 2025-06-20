FROM mcr.microsoft.com/playwright/python:v1.43.1-focal

# Set work directory
WORKDIR /app

# Copy everything to container
COPY . .

# Install Python packages
RUN pip install --upgrade pip && pip install -r requirements.txt

# Set environment variable for Playwright
ENV PYTHONUNBUFFERED=1

# Run playwright install (already included in base image but added for safety)
RUN playwright install

# Start command
CMD ["python", "main.py"]
