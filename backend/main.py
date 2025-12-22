from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import json
from agent import graph
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]

class ChatResponse(BaseModel):
    messages: List[Message]

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

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    try:
        input_messages = map_to_langchain_messages(request.messages)
        
        async def event_generator():
            async for event in graph.astream_events({"messages": input_messages}, version="v1"):
                kind = event["event"]
                # print(f"DEBUG EVENT: {kind}", flush=True) # Debug log
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        yield f"data: {json.dumps({'content': content})}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        input_messages = map_to_langchain_messages(request.messages)
        final_state = graph.invoke({"messages": input_messages})
        output_messages = map_from_langchain_messages(final_state["messages"])
        return ChatResponse(messages=output_messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
