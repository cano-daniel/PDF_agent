FROM python:3.11-slim

WORKDIR /app

# Primero los requerimientos para aprovechar la caché de capas de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia de archivos individuales
COPY agent_app.py .
#COPY .env .

# Copia de la carpeta utils manteniendo su estructura
COPY utils/ ./utils/

EXPOSE 8000

CMD ["uvicorn", "agent_app:app", "--host", "0.0.0.0", "--port", "8000"]