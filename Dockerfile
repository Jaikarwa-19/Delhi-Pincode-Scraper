FROM mcr.microsoft.com/playwright/python:v1.43.1-focal

# Set working directory
WORKDIR /app

# Copy everything to the container
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# (Redundant but safe) Ensure Playwright dependencies are installed
RUN playwright install

# Run your script
CMD ["python", "main.py"]
