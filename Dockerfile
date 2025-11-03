# Use the official Python 3.11 slim image as the base
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (for Reflex, Bun, and npm)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    unzip \
    curl \
    libstdc++6 \
    libc6 \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first (optimization for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy only the necessary Reflex app files and directories
COPY rxconfig.py .
COPY Cloud_Kinetics/ ./Cloud_Kinetics/
COPY assets/ ./assets/
COPY .web/ ./.web/

# Ensure the app sees the intended ports inside the container
EXPOSE 3000 8000

# Command to run the Reflex app
CMD ["reflex", "run", "--env", "prod"]