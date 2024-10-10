# Use miniconda3 base image
FROM continuumio/miniconda3:4.9.2

# Install dependencies, including RDKit and any other requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Set the working directory inside the container
WORKDIR /app

# Copy the application source code into the container
COPY src/ .

# Create a non-root user and Change ownership of the /app directory to the new user
RUN useradd -m nonrootuser \
  && chown -R nonrootuser:nonrootuser /app

# Switch to the non-root user
USER nonrootuser

# Expose the port the app runs on
EXPOSE 8080

# Command to run the FastAPI application with non-root user privileges
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
