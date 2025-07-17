# Use an official Python base image
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your bot code
COPY . .

# Expose default port (optional)
EXPOSE 8080

# Run your bot
CMD ["python", "bot.py"]
