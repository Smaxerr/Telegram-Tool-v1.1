# ✅ Use official Playwright image with Python 3.11 and Chromium/Firefox/WebKit pre-installed
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the bot code
COPY . .

# Optional: Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Expose port (optional — only if using webhooks or HTTP)
EXPOSE 8080

# Run the bot
CMD ["python", "bot.py"]
