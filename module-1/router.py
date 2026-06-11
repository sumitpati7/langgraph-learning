# ---------------------------------------------------------------------------
# Router: Tool-calling LLM with LangGraph
#
# This script builds a conversational agent that:
#   1. Prompts the user for input (via console)
#   2. Sends the input to an LLM (Anthropic Claude) that has a `multiply` tool
#   3. Routes tool calls to the tool node and loops back, or ends on a final answer
#   4. Displays the final response with rich formatting
#
# Suggested improvements for a polished UX:
#   - Wrap the graph invoke in a retry/error loop so failures don't crash
#   - Add a streaming variant for real-time token display
#   - Add a conversation history manager (persist messages between turns)
#   - Add a graceful exit command (e.g., typing "exit" or "quit")
#   - Use a .env fallback with clear error when model key is missing
#   - Add typing indicators or spinner while waiting for the LLM
#   - Replace hardcoded image path with dir-creation logic
#   - Add CLI argument support (e.g., --model, --temperature)
# ---------------------------------------------------------------------------

import dotenv
# import os
import logging

logger = logging.getLogger("langgraph")
logger.setLevel(logging.INFO)

handler = logging.FileHandler("logs/router.log")
logger.addHandler(handler)

from rich.live import Live
from langchain_ollama import ChatOllama
from langchain_anthropic import ChatAnthropic
from langchain.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console(stderr=True)

# Load environment variables (API keys, etc.)
dotenv.load_dotenv()

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


def get_user_prompt(state: MessagesState):
    """Prompt the user for input and return it as a HumanMessage."""
    prompt = "Wha t is the produc tof 3, 4 and 16"
    return {
        "messages": [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=prompt)
        ]
    }


def multiply(a: int, b: int) -> int:
    """Multiplies a and b and returns the product.
    Args:
        a: first int
        b: second int
    """
    return a * b

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------
# This is the llm that is to be used when using the graph.
# Since this a light weight operation local model using 
# ollama works just fine, note that the model should be able
# to make tool calls. 

# https://ollama.com/library/qwen3
# llm = ChatOllama(
#     model="qwen3:1.7b",
#     temperature=1,
# )

llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    temperature=1
)
llm_with_tools = llm.bind_tools([multiply])


def tool_calling_llm(state: MessagesState):
    """Invoke the LLM — may return a text response or a tool-call request."""
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


# ---------------------------------------------------------------------------
# Build the LangGraph
# ---------------------------------------------------------------------------
builder = StateGraph(MessagesState)
builder.add_node("get_user_prompt", get_user_prompt)
builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_node("tools", ToolNode([multiply]))
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

# Export the graph as a PNG for documentation / visualisation
graph.get_graph().draw_mermaid_png(output_file_path="image/graph.png")

def generate_status_panel(message):
    return Panel(
        Markdown(message),
        title="[bold reverse] Live Dashboard [/bold reverse]"
    )

# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------
response = ""
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

            live.update(generate_status_panel(response))
                
                
                
# 

