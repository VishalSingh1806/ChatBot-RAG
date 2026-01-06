# Use a lightweight official Python image
FROM python:3.10-slim

# Set working directory inside container
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port (FastAPI default)
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
