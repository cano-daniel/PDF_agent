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
    """Searches on the RAG what chunk of text is relevant to the query and the _n tells the ranking order
    
    Args:
        pages: List of pages to search for
    Returns:
        Dict: List of relevant chunks of text
    """
    RAGresults = local_RAG.search_by_page(pages)
    result = {}
    i = 0
    for RAGresult in RAGresults:
        i += 1
        for key, value in RAGresult.items():
            result[key + str(i)] = value
    return result



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

# Step 3: Define model node
from langchain.messages import SystemMessage


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


# Step 4: Define tool node

from langchain.messages import ToolMessage


def tool_node(state: dict):
    """Performs the tool call"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}

# Step 5: Define logic to determine whether to end

from typing import Literal
from langgraph.graph import StateGraph, START, END


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

# Step 6: Build agent

# Build workflow
agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)
agent_builder.add_edge("tool_node", "llm_call")

# Compile the agent
agent = agent_builder.compile()


if __name__ == "__main__":
    # La instancia se crea SOLO en el proceso principal

    # Pregunta de prueba
    user_input = "Tell me about support vector machines, how do they work, and where on the pdf can I find the information? especificly tell me the optimization problem"
    
    initial_state = {"messages": [HumanMessage(content=user_input)], "llm_calls": 0}
    
    # Ejecución
    final_state = agent.invoke(initial_state)
    
    print("\n" + "="*50)
    for m in final_state["messages"]:
        m.pretty_print()