# Use Python 3.9 as the base image
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the project files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000 (since Render routes requests internally)
EXPOSE 8000

# Run Gunicorn with HTTPS support
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--certfile=cert.pem", "--keyfile=key.pem", "wsgi:app"]

# Run Gunicorn without SSL (Render provides HTTPS)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "wsgi:app"]
