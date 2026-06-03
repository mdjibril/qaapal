# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements first to leverage Docker caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose port 8080 (Cloud Run's default port)
EXPOSE 8080

# Command to run Streamlit on container startup
# Disabling CORS/Xsrf prevents "Connection Refused" issues on GCP
CMD ["streamlit", "run", "main.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]