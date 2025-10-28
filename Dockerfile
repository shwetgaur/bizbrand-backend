# Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8080

# Run the app! Google Cloud Run will set the $PORT variable.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]