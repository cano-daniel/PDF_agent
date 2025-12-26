# Dockerfile - Instructions for building our Docker image
# Think of this as a recipe that tells Docker how to create a container with our app

# Start with a base Python image
# python:3.11-slim is a lightweight version of Python 3.11
# "slim" means it has fewer pre-installed packages, making it faster to download
FROM python:3.11-slim

# Set the working directory inside the container
# All subsequent commands will run from this directory
# This is like doing "cd /app" in a terminal
WORKDIR /app

# Copy requirements.txt first
# We do this separately to take advantage of Docker's layer caching
# If requirements don't change, Docker won't reinstall packages on rebuild
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir reduces the image size by not storing pip's cache
# This makes our final container smaller and faster to distribute
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of our application code
# This includes app.py and the templates folder
COPY . .

# Expose port 5000
# This tells Docker that our app listens on port 5000
# It's documentation - the actual binding happens in app.py
EXPOSE 5000

# Set environment variables
# FLASK_APP tells Flask which file contains our application
# PYTHONUNBUFFERED ensures Python prints appear in Docker logs immediately
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# The command to run when the container starts
# This starts our Flask application
CMD ["python", "app.py"]