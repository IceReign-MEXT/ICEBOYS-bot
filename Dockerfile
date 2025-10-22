# nano Dockerfile
# (PASTE THE CONTENT BELOW)

# Use Python 3.12 slim as base
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for the Webhook listener (Render requirement)
EXPOSE 5000

# Run the bot's monetization script
CMD ["python", "iceboys_monetizer.py"]
