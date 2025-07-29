# Use a lightweight official Python image
FROM python:3.9-slim

# Set working directory inside container
WORKDIR /app

# Copy only the requirements file to leverage Docker cache
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip && pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port (FastAPI default)
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
