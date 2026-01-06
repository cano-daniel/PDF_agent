"""
Simple Math Agent - Learn LangGraph Basics
WITH DEBUGGING AND VISUALIZATION
"""

from typing import TypedDict, Annotated
import operator
import os
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from dotenv import load_dotenv
from langchain.messages import ToolMessage
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langchain.messages import SystemMessage
from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
import operator
import json

# Load environment variables from .env file
load_dotenv()


# Step 1: Define tools and model

from langchain.tools import tool
from langchain.chat_models import init_chat_model
from RAG import LocalRAGAgent

local_RAG = LocalRAGAgent() 

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite",
    temperature=0
)

#tool definition 

@tool
def search(query: str, k:int = 3) -> dict:
    """Searches on the RAG what chunk of text is relevant to the query and the _n tells the ranking order
    
    Args:
        query: The query to search for
        k: Number of chunks to return
    Returns:
        dict: List of relevant chunks of text
    """
    RAGresults = local_RAG.search(query,k)
    result = {}
    i = 0
    for RAGresult in RAGresults:
        i += 1
        for key, value in RAGresult.items():
            result[key + str(i)] = value
    return result

@tool
def search_by_page(pages: list[int]) -> dict:
    """Returns the full text of specific pages from the PDF to provide a summary or detail.
    
    Args:
        pages: List of page numbers (integers) to retrieve.
    Returns:
        dict: A dictionary where keys are page numbers and values are the text content.
    """
    # 1. Llamamos al método correcto de la clase (return_by_page)
    # Importante: Asegúrate de que 'local_RAG' sea la instancia de tu clase
    content_dict = local_RAG.return_by_page(pages)
    
    # 2. Simplemente devolvemos el diccionario. 
    # El LLM es lo suficientemente inteligente para leer este JSON.
    return content_dict



# Augment the LLM with tools
tools = [search, search_by_page]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)

# Step 2: Define state

from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
import operator


class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with performing a search on a pdf of machine leaning so you should act like a machine leaning expert and based your answers on the pdf"
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }

def tool_node(state: dict):
    """Performs the tool call"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}

# Conditional edge function to route to the tool node or end based upon whether the LLM made a tool call
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "tool_node"

    # Otherwise, we stop (reply to the user)
    return END


from langgraph.checkpoint.memory import MemorySaver

class dummy_agent():
    def __init__(self):
        # 1. Initialize the checkpointer
        self.memory = MemorySaver()
        self.agent = self._agent_initializer()
        # 2. Set a default thread_id (like a session ID)
        self.thread_id = "default_user_1"
        self.config = {"configurable": {"thread_id": self.thread_id}}

    def _agent_initializer(self):
        agent_builder = StateGraph(MessagesState)
        
        agent_builder.add_node("llm_call", llm_call)
        agent_builder.add_node("tool_node", tool_node)

        agent_builder.add_edge(START, "llm_call")
        agent_builder.add_conditional_edges(
            "llm_call",
            should_continue,
            ["tool_node", END]
        )
        agent_builder.add_edge("tool_node", "llm_call")

        # 3. Compile with the checkpointer
        return agent_builder.compile(checkpointer=self.memory)
    
    def clear_state(self):
        """Clears memory by changing the thread ID (starting a fresh conversation)"""
        import uuid
        # Generating a new ID is the cleanest way to 'clear' a checkpoint
        self.thread_id = str(uuid.uuid4())
        self.config = {"configurable": {"thread_id": self.thread_id}}
        print(f"Memory cleared. New session started: {self.thread_id}")

    def permanent_delete_all_memory(self):
        """Permanently deletes all memory"""
        # Esto borra físicamente todos los datos guardados en el checkpointer de RAM
        self.memory.storage.clear()
        print("Todos los registros del checkpointer han sido eliminados físicamente.")

    def run_chat(self, user_input: str):
        """Runs the agent with automatic memory via checkpointer"""
        # We only send the NEW message. 
        # The agent uses the thread_id in self.config to find past history.
        input_data = {"messages": [HumanMessage(content=user_input)]}
        
        # We invoke using the config (thread_id)
        final_output = self.agent.invoke(input_data, config=self.config)
        
        return final_output["messages"][-1].content

if __name__ == "__main__":
    # La instancia se crea SOLO en el proceso principal

    # Pregunta de prueba
    print('nothing')