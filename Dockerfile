# Use a verified Playwright image with all browser dependencies
FROM mcr.microsoft.com/playwright/python:v1.43.1-jammy

# Set working directory
WORKDIR /app

# Copy all project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser binaries
RUN playwright install

# Set environment variable (you can remove this if setting it from Render UI)
# ENV GOOGLE_MAPS_API_KEY=your-key-here

# Run the main script
CMD ["python", "main.py"]
