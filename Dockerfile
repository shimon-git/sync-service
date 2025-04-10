# Use official Python image
FROM python:3.13-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements first (to cache dependencies)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY *.py .

# Expose the FastAPI port (adjust if needed)
EXPOSE 5000

# Set the default command to run the app
CMD ["python", "-u", "main.py"]