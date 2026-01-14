# === web handler ===
# utilities for the web handler
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
import os

# === agent ===
# custom agent class
from utils.agent import dummy_agent #agent class

# agent initialization
agent = dummy_agent()

# web handler initialization
app = FastAPI()

# Define the shape of the data we expect
class Query(BaseModel):
    text: str
    User_id: str = "default_user"

@app.get("/")
def read_root():
    return {"status": "Online", "message": "FastAPI is running correctly inside Docker "}

@app.post("/search")
def run_search(query: Query):

    # Here you would call your LocalRAGAgent
    agent_message = agent.run_chat(
        user_input= query.text, 
        user_name= query.User_id
        )

    return {
        "mesagge": agent_message
    }

@app.get("/get-pdf")
async def get_pdf(file_name: str):
    pdf_path = "local_rag/pdf_files/" + file_name # Ruta al PDF en el contenedor del agente
    
    if os.path.exists(pdf_path):
        # Retorna el archivo con el tipo de contenido correcto
        return FileResponse(
            path= pdf_path, 
            media_type= 'application/pdf', 
            filename= file_name + ".pdf"
        )
    return {"error": "Archivo no encontrado"}

