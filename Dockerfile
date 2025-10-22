# Use Python 3.12 slim as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install build-essentials (CRITICAL FIX for compiling C extensions like lru-dict)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for the Webhook listener (Render requirement)
EXPOSE 5000

# Run the bot's monetization script
CMD ["python", "iceboys_monetizer.py"]
