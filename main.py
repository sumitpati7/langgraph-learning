import dotenv
import os

from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from langchain.messages import HumanMessage, AIMessageChunk, AIMessage

dotenv.load_dotenv()

def main():
    print("Hello from langchain-academy-learning!")


if __name__ == "__main__":
    main()
