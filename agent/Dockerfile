FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent_app.py .
COPY utils/ ./utils/
COPY local_rag/ ./local_rag/

# The port your app listens on
EXPOSE 8000

CMD ["uvicorn", "agent_app:app", "--host", "0.0.0.0", "--port", "8000"]