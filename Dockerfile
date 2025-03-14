# Use Python 3.9
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy project files into the container
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Expose port 5000 for HTTPS
EXPOSE 5000

# Run Gunicorn with HTTPS support
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--certfile=cert.pem", "--keyfile=key.pem", "wsgi:app"]
