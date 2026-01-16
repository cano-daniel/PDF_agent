# Agent Service Documentation (FastAPI)

The **Agent Service** is the "Brain" of the application. It handles the heavy lifting: processing PDFs, searching through text using Vector Databases, and generating AI responses using LangGraph and Google Gemini.

---

## API Endpoints

| Route | Method | Description |
| :--- | :--- | :--- |
| `/` | `GET` | Health check to verify the container is online. |
| `/search` | `POST` | Primary entry point. Receives user text and returns the AI agent's response. |
| `/get-pdf` | `GET` | Serves the physical PDF file to the Flask service for display in the UI. |

---

## Internal Architecture & Classes

The service is built on three main layers that work together to provide accurate answers:

### 1. The Controller: FastAPI & Pydantic
* **`Query` (Class)**: A Pydantic model that validates the incoming data. It ensures the Flask app sends exactly what the agent needs (`text` and `User_id`).
* **Web Handler**: Manages the HTTP communication and handles file streaming for the PDF viewer.

### 2. The Logic: `dummy_agent` (LangGraph)
This class manages the "Thought Process" of the AI. Instead of a single prompt, it uses a **State Graph** to decide its next move.



* **`MessagesState`**: Keeps track of the conversation history and model usage.
* **`llm_call` (Function)**: The brain node where the Gemini model analyzes the user question.
* **`should_continue`**: A conditional logic gate. If the AI needs more info, it goes to the tools; if it has the answer, it goes to the user.
* **`MemorySaver`**: Persistent storage that allows the AI to remember what you said 5 minutes ago using a `thread_id`.

### 3. The Knowledge: `LocalRAGAgent` (RAG System)
This class manages the document "Memory" using Retrieval-Augmented Generation (RAG).



* **`RecursiveCharacterTextSplitter`**: Chops PDFs into small pieces (1000 characters) so the AI can find specific paragraphs quickly.
* **`HuggingFaceEmbeddings`**: Uses the `BAAI/bge-m3` model to turn text into "Vectors" (mathematical coordinates).
* **`Chroma`**: A Vector Database that stores these coordinates. When you ask a question, Chroma finds the text pieces with the closest coordinates.

---

## Specialized AI Tools
The Agent is not just a chatbot; it has "hands" (Tools) it can use to look at your data:

1.  **`search`**: The agent uses this to find the most relevant "chunks" of text across the entire PDF.
2.  **`search_by_page`**: The agent uses this when it needs to read a full page (like a conclusion or a specific table) to give a more detailed summary.

---

## Environment Configuration
To work correctly, this service requires:
* `GOOGLE_API_KEY`: For the Gemini-2.5-Flash-Lite model.
* `local_rag/`: A persistent volume where the indexed PDFs and Vector Database are stored.