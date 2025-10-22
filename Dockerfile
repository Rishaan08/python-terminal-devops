# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY executor.py .
COPY cli.py .
COPY webapp.py .

# Copy templates directory
COPY templates/ templates/

# Create /tmp directory for the terminal to work in
RUN mkdir -p /tmp && chmod 777 /tmp

# Expose port 5001
EXPOSE 5001

# Set environment variables
ENV FLASK_APP=webapp.py
ENV PYTHONUNBUFFERED=1

# Run the Flask web application
CMD ["python", "webapp.py"]