# Flask Service Documentation

The **Flask Service** acts as the middleware and web server for the AI PDF Research Assistant. It manages the user interface, maintains a temporary chat history, and serves as a proxy to the AI Agent Service.

## Core Functionalities

* **Request Proxying:** Forwards user messages to the FastAPI Agent and returns AI-generated responses.
* **Session Memory:** Stores an in-memory list of `chat_history` to keep the conversation flowing during a session.
* **PDF Synchronization:** Downloads PDF files from the Agent container and saves them to the local `static/` folder for browser display.
* **Logging:** Integrated Python logging for tracking API calls and system errors.

---

## API Endpoints

| Route | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Serves the main `index.html` interface. |
| `/api/send` | `POST` | Receives user text, communicates with the Agent, and saves the interaction. |
| `/api/history` | `GET` | Returns all messages stored in the current session. |
| `/api/clear` | `POST` | Resets the `chat_history` list. |
| `/api/get-pdf/<file>`| `GET` | Fetches a specific PDF from the Agent Service and stores it locally. |

---

## ⚙️ Configuration
The service relies on a `.env` file for discovery within the Docker network:
* `AGENT_SERVICE_HOST`: The internal hostname of the FastAPI container.
* `AGENT_SERVICE_PORT`: The port where the Agent Service is listening (usually 8000).