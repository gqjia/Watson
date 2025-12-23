from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]
    coach_draft: str
    critic_feedback: str
    mentor_advice: str
    search_results: str  # New field to store search results for frontend
    revision_count: int
