# === web handler ===
# utilities for the web handler
from fastapi import FastAPI
from pydantic import BaseModel

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