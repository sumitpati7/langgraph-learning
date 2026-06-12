## Chapter agent in module-1 of langgraph.

# In this chapter, the router module we created beforehand is implement.
# The router chapter was meant to teach how to add conditional nodes.
# I had already implemented the agent. An agent is just an llm that is
# capable of deciding whether it should make an tool call or the output is
# finalised enough to present it to the user i.e. respond to the user.

## Load env variables for API keys
import dotenv
dotenv.load_dotenv()

# Implement logging to the file
import logging
logger = logging.getLogger("langgraph")
logger.setLevel(logging.INFO)
# determines how logs are handled
handler = logging.FileHandler("logs/agent.log")
logger.addHandler(handler)

from rich.live import Live
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# System-level instructions for the LLM
sys_prompt = """
You are a helpful assistant.

Response formatting rules:
- Do not use LaTeX syntax. Avoid `$...$`, `$$...$$`, `\\frac`, `\\times`, `\\boxed`, or any other LaTeX commands.
- Use plain Markdown only.
- Use Unicode symbols where appropriate (for example, use × instead of \\times).
- Use Markdown formatting such as headings, bold text, bullet points, and code blocks when useful.
- Provide an elaborative explanation of the reasoning/process step by step.
- Make the response easy to render using Rich Markdown.
"""

from langchain.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import MessagesState

user_input: str = ""

def get_user_prompt(state: MessagesState):
    """Prompt the user for input and return it as a HumanMessage."""
    return {
        "messages": [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_input)
        ]
    }
    
## Tools definition

def multiply(a: int, b: int) -> int:
    """Multiplies a and b and returns the product.
    Args:
        a: first int
        b: second int
    """
    return a * b
  
def add(a: int, b: int) -> int:
    """Adds a and b and returns the sum.
    Args:
        a: first int
        b: second int
    """
    return a + b
  
def subtract(a: int, b: int) -> int:
    """subtracts a and b and returns the difference.
    Args:
        a: first int
        b: second int
    """
    return a - b
  
def divide(a: int, b: int) -> int:
    """Multiplies a and b and returns the product.
    Args:
        a: first int
        b: second int
    """
    return a / b
  
## LLM defintion
from langchain_ollama import ChatOllama


llm = ChatOllama(
  model="qwen3.5:2b",
  temperature=1
)
tools = [add, multiply, divide, subtract]
# bind the tools to the llm
llm_with_tools = llm.bind_tools(tools)

def tool_calling_llm(state: MessagesState):
    """Invoke the LLM — may return a text response or a tool-call request."""
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

from langgraph.graph import START, StateGraph
from langgraph.prebuilt import tools_condition
from langgraph.prebuilt import ToolNode
# from IPython.display import Image, display

builder = StateGraph(MessagesState)
builder.add_node("get_user_prompt", get_user_prompt)
builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_node("tools", ToolNode(tools))
builder.add_edge(START, "get_user_prompt")
builder.add_edge("get_user_prompt", "tool_calling_llm")
builder.add_conditional_edges(
    "tool_calling_llm",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", "tool_calling_llm")

graph = builder.compile()

graph.get_graph().draw_mermaid_png(output_file_path="image/agent.png")

def generate_status_panel(message):
    return Panel(
        Markdown(message),
        title=f"[bold reverse] {user_input} [/bold reverse]"
    )
    
response = ""
user_input = input("Enter a mathematical problem: ")

from helper.latex_remover import clean_latex_math

with Live(generate_status_panel(response), refresh_per_second=10) as live:
    for chunk in graph.stream(
        {},
        stream_mode=["updates", "custom", "messages"],
        version="v2"
    ):
        if chunk["type"] == "updates":
            for node_name, state in chunk["data"].items():
                message = f"[{node_name} Node]: {state}"
                logger.info(message)
                live.console.print(f"[grey50]{message}")
        elif chunk["type"] == "custom":
            message = f"Status:\t\t {chunk['data']['status']}"
            logger.info(message)
            live.console.print(f"[grey50]{message}")
        elif chunk["type"] == "messages":
            message, metadata = chunk["data"]

            if isinstance(message, AIMessage):
                content = message.content

                if not isinstance(content, list):
                    if isinstance(content, str):
                        response += content
                        # print(content)

                for block in content:
                    if (
                        isinstance(block, dict)
                        and block.get("type") == "text"
                        and block.get("text")
                    ):
                        response += block["text"]
                        # print(block["text"])

            live.update(generate_status_panel(clean_latex_math(response)))
