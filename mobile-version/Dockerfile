FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for imap and build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Make start script executable
RUN chmod +x start.sh

# Expose the standard HF port
EXPOSE 7860

# Run the start script
CMD ["./start.sh"]
