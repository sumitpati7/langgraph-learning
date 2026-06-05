import dotenv
import os

from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain.messages import HumanMessage, AIMessageChunk, AIMessage
from IPython.display import Image, display
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition

dotenv.load_dotenv()

def multiply(a: int, b: int) -> int:
    """Multiplies a and b and returns the product.
    Args:
        a: first int
        b: second int
    """
    
    return a * b
    

llm = ChatOllama(
    model="qwen3:1.7b",
    temperature=0
)
llm_with_tools = llm.bind_tools([multiply])

def tool_calling_llm(state: MessagesState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

builder = StateGraph(MessagesState)
builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_node("tools", ToolNode([multiply]))
builder.add_edge(START, "tool_calling_llm")
builder.add_conditional_edges(
    "tool_calling_llm",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", END)
graph = builder.compile()

# View
graph.get_graph().draw_mermaid_png(output_file_path="image/graph.png")
