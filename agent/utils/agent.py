"""
Simple Math Agent - Learn LangGraph Basics
WITH DEBUGGING AND VISUALIZATION
"""

# === SYSTEM & ENVIRONMENT ===
# Basic utilities for the OS and environment variables
import os
import json
import operator
from dotenv import load_dotenv

# === TYPING & STRUCTURE ===
# Defining the shapes of our data and state
from typing import Literal, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage # LangChain messages

# === AGENT TOOLS & RAG ===
# Logic for the functions the agent can call and your custom PDF logic
from langchain_core.tools import tool  # LangChain tools
from utils.RAG import LocalRAGAgent  # custom local module

# === ZONE 4: THE BRAIN (LLM) ===
# Connection to Google Gemini and model initialization
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chat_models import init_chat_model

# === THE GRAPH (LANGGRAPH) ===
# Orchestration of the agent's flow and memory
from langgraph.graph import StateGraph, START, END # LangGraph default states
from langgraph.prebuilt import ToolNode # LangGraph prebuilt node
from langgraph.checkpoint.memory import MemorySaver # LangGraph memory saver


# Load environment variables from .env file
load_dotenv()

# global RAG used o the agent class
local_RAG = LocalRAGAgent() 

# initialization of the api conection to the llm model
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", #gemini-2.5-flash-lite
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


# this is a custom dictionary to manage the chat history of the agent (also the state)
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int

# funtions that will be used as nodes for the agent
def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""
    
    # Definimos las instrucciones de formato
    system_prompt = '''
        You are an expert research assistant. Your task is to answer questions based strictly on the provided PDF context.

        FORMATTING RULES:
        1. Use Markdown for structure (headers, bold, lists).
        2. MATH: 
        - Inline: Use single dollar signs ($E=mc^2$).
        - Block: Use double dollar signs ($$formula$$).
        
        3. CITATIONS (IN-TEXT): 
        - Every time you use information, add a numerical citation using this exact format: [[n]](filename.pdf#page=X).
        - IMPORTANT: Replace all spaces in the filename with underscores (_).
        - Example: "Trees minimize entropy by splitting the feature space [[1]](main_notes.pdf#page=10)."

        4. REFERENCES SECTION:
        - At the very end of your response, add a horizontal rule `---`.
        - Create a section titled "**Referencias:**".
        - List every document used with the format: * [[n] Source: Filename, Page: X](filename.pdf#page=X).
        - Ensure the filenames in the references also have underscores instead of spaces.

        STRICT CONSTRAINTS:
        - Use the 'source' and 'page' fields from the metadata provided in the context.
        - The link MUST follow the pattern: filename.pdf#page=number
        - If the answer is not in the PDF context, state that you do not have enough information.
        '''

    return {
        "messages": [
            model_with_tools.invoke(
                [SystemMessage(content=system_prompt)] + state["messages"]
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


# class of the agent
class dummy_agent():
    def __init__(self, user_name = "default_user"):
        """inicializes the class compi;inmg the agnet and doing the configuration
        
        Args:
            user_name: The name of the user
        Returns:
        dummy_agent: class to chat
        """
        # 1. Initialize the checkpointer
        self.memory = MemorySaver()
        self.agent = self._agent_initializer()
        # 2. Set a default thread_id (like a session ID)
        self.thread_id = user_name
        self.config = {"configurable": {"thread_id": self.thread_id}}

    def _agent_initializer(self):
        """initializes the agent generating a graph of nodes and edges"""
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

    def run_chat(self, user_input: str, user_name: str = 'default_user'):
        """Runs the agent with automatic memory via checkpointer
        
        Args:
            user_input: The user input
            user_name: The user name
        Returns:
            final_output: The final output of the agent
        """

        #check_user
        if user_name != 'default_user':
            self.thread_id = user_name
            self.config = {"configurable": {"thread_id": self.thread_id}}
        # We only send the NEW message. 
        # The agent uses the thread_id in self.config to find past history.
        input_data = {"messages": [HumanMessage(content=user_input)]}
        
        # We invoke using the config (thread_id)
        final_output = self.agent.invoke(input_data, config=self.config)
        
        return final_output["messages"][-1].content

if __name__ == "__main__":
    dummy = dummy_agent()
    message = input("User: ")
    print(dummy.run_chat(message))