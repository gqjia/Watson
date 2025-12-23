from typing import List
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from schemas import Message

def map_to_langchain_messages(messages: List[Message]) -> List[BaseMessage]:
    result = []
    for m in messages:
        if m.role == "user":
            result.append(HumanMessage(content=m.content))
        elif m.role == "assistant":
            result.append(AIMessage(content=m.content))
        elif m.role == "system":
            result.append(SystemMessage(content=m.content))
    return result

def map_from_langchain_messages(messages: List[BaseMessage]) -> List[Message]:
    result = []
    for m in messages:
        role = "user"
        if isinstance(m, AIMessage):
            role = "assistant"
        elif isinstance(m, SystemMessage):
            role = "system"
        elif isinstance(m, HumanMessage):
            role = "user"
        result.append(Message(role=role, content=str(m.content)))
    return result
