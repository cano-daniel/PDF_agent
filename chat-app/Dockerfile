# 1. Use Python 3.11 (Slim version to keep it small)
FROM python:3.11-slim

# 2. Create and move into the /app folder
WORKDIR /app

# 3. Copy just the library list first (helps build faster next time)
COPY requirements.txt .

# 4. Install the libraries
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy all your project files into the image
COPY . .

# 6. Inform Docker we use port 5000
EXPOSE 5000

# 7. Set settings: point to app.py and show logs in real-time
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# 8. Start the Flask app
CMD ["python", "app.py"]