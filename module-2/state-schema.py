"""
# STATE SCHEMA
- State schema represents the structure and types of data that our graph will use.
- All nodes communicate with each other via the state schema

## Define
We can define a state schema with one of the three methods: `TypedDict`, `Dataclass`, and `Pydantic`.
In this and the module's after I will try to use `Pydantic`. The reason I chose pydantic over other
two is because pydantic provides ways of validating data. But the easiest one
"""

import random
from IPython.display import Image, display
from langgraph.graph import StateGraph, START, END
from rich.console import Console
from pydantic import BaseModel, field_validator, ValidationError

class PydanticState(BaseModel):
    name: str
    mood: str | None = None
    
    @field_validator('mood')
    @classmethod
    def validate_mood(cls, value):
        if value and value not in ["happy", "sad"]:
            raise ValueError("[red]Mood[/red] can be either 'happy' or 'sad'.")
        return value

console = Console()

def happy_node(state: PydanticState):
    console.print("---------------------Happy Node---------------------")
    return {"mood": "happy"}
  
def sad_node(state: PydanticState):
    print("---------------------Sad Node---------------------")
    # return {"mood": "mad"}
    return {"mood": "sad"}
  
def decision_edge(state: PydanticState) -> str:
    print("---------------------Decision Node---------------------")
    
    if random.random() > 0.5:
        return "happy_node"
      
    return "sad_node"
  
def print_node(state: PydanticState):
    print("---------------------Print Node---------------------")
    console.print(f"[bold]{state.name}[/bold] is [bold]{state.mood}[/bold]")
    
builder = StateGraph(PydanticState)
builder.add_node("happy_node", happy_node)
builder.add_node("sad_node", sad_node)
# builder.add_node("decision_node", decision_node)
builder.add_node("print_node", print_node)

# Logic
# builder.add_edge(START, "decision_node")
builder.add_conditional_edges(START, decision_edge, {
        "happy_node": "happy_node",
        "sad_node": "sad_node",
    })
builder.add_edge("sad_node", "print_node")
builder.add_edge("happy_node", "print_node")
builder.add_edge("print_node", END)

graph = builder.compile()

graph.get_graph().draw_mermaid_png(output_file_path="image/state-schema.png")

try:
    graph.invoke({"name": "Sumit"})
except ValidationError as e:
    for error in e.errors():
        field = error["loc"][0]
        message = error["msg"]

        console.print(f"[bold red]{field}[/bold red]: {message}")
    