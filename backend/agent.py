from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from dotenv import load_dotenv
import os

load_dotenv()

class State(TypedDict):
    messages: Annotated[list, add_messages]

# Configure Deepseek
# Using "deepseek-chat" as the model name, adjust if necessary.
llm = ChatOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    model="deepseek-chat", 
    temperature=0.7,
    streaming=True
)

SYSTEM_PROMPT = """You are a helpful Interview Preparation Assistant. 
Your goal is to help the user review and prepare for technical interviews (Software Engineering).

You should:
1. Help the user clarify technical concepts.
2. Provide mock interview questions if requested, but act as a coach, not a strict interviewer.
3. Review the user's answers and provide constructive feedback, pointing out missing details or alternative approaches.
4. Be encouraging and supportive.
5. If the user asks about a specific topic, explain it clearly with examples.

Start by introducing yourself as an Interview Prep Assistant and ask the user what topic they would like to review or if they want to try a mock question."""

async def assistant(state: State, config: RunnableConfig):
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    response = await llm.ainvoke(messages, config)
    return {"messages": [response]}

builder = StateGraph(State)
builder.add_node("assistant", assistant)
builder.add_edge(START, "assistant")
builder.add_edge("assistant", END)

graph = builder.compile()
