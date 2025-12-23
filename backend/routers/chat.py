from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
import uuid
from agent import get_graph, get_all_threads, summarize_thread
from schemas import ChatRequest, ChatResponse
from utils import map_to_langchain_messages, map_from_langchain_messages

router = APIRouter()

@router.get("/threads")
async def get_threads():
    try:
        threads = await get_all_threads()
        return {"threads": threads}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{thread_id}")
async def get_chat_history(thread_id: str):
    try:
        graph = await get_graph()
        state = await graph.aget_state({"configurable": {"thread_id": thread_id}})
        
        if not state.values:
            return {"messages": []}
            
        messages = state.values.get("messages", [])
        output_messages = map_from_langchain_messages(messages)
        return {"messages": output_messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def chat_stream(request: ChatRequest):
    try:
        input_messages = map_to_langchain_messages(request.messages)
        
        # Configure thread_id
        thread_id = request.thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        # Initialize graph lazily
        graph = await get_graph()

        async def event_generator():
            async for event in graph.astream_events({"messages": input_messages}, config=config, version="v1"):
                kind = event["event"]
                name = event.get("name")
                
                # Check for node start to signal new revisions
                if kind == "on_chain_start":
                    # LangGraph nodes often appear as on_chain_start with the node name
                    if name == "generate_draft":
                        yield f"data: {json.dumps({'type': 'revision_start', 'node': 'coach_draft'})}\n\n"
                    elif name == "critique_draft":
                        yield f"data: {json.dumps({'type': 'revision_start', 'node': 'critic'})}\n\n"
                
                if kind == "on_tool_end":
                    # We want to capture the tool output for "web_search"
                    # name is the tool name (e.g., "web_search")
                    if name == "web_search":
                         # The output is in event["data"]["output"]
                         # It might be a ToolMessage or just the string output depending on how it's invoked.
                         # Based on our run_with_tools, we invoke it directly, so it returns a string.
                         # But wait, astream_events captures the tool node execution if it's a node?
                         # Or if it's called within a node?
                         # If we manually invoke tool in run_with_tools, it might NOT trigger on_tool_end automatically 
                         # UNLESS we use the compiled graph's tool node or if we are inside a traced context.
                         
                         # However, we are manually appending ToolMessages.
                         # But we also called `web_search.invoke(tool_args)`. Since `web_search` is a @tool, it is a Runnable.
                         # So it should emit events.
                         
                         output = event["data"].get("output")
                         if output:
                             # output is likely the return string of the tool
                             # We want to stream this to the frontend as "search_results"
                             # We can use a special node name for this, e.g., "search"
                             yield f"data: {json.dumps({'content': str(output), 'node': 'search'})}\n\n"

                if kind == "on_chat_model_stream":
                    # Check metadata for node name
                    metadata = event.get("metadata", {})
                    # node_name in metadata is usually the graph node name (e.g., generate_draft)
                    # We need to map it to the frontend expected role names (coach_draft, critic, coach)
                    
                    tags = event.get("tags", [])
                    node_name = ""
                    
                    if "coach_draft" in tags:
                        node_name = "coach_draft"
                    elif "critic" in tags:
                        node_name = "critic"
                    elif "coach" in tags:
                        node_name = "coach"
                    elif "mentor" in tags:
                        node_name = "mentor"
                    
                    # Fallback to metadata if tags are missing (should not happen with our setup)
                    if not node_name:
                         node_id = metadata.get("langgraph_node", "")
                         if node_id == "generate_draft":
                             node_name = "coach_draft"
                         elif node_id == "critique_draft":
                             node_name = "critic"
                         elif node_id == "generate_final":
                             node_name = "coach"
                         elif node_id == "mentor":
                             node_name = "mentor"

                    if node_name:
                        content = event["data"]["chunk"].content
                        if content:
                            yield f"data: {json.dumps({'content': content, 'node': node_name})}\n\n"
                            
            yield "data: [DONE]\n\n"
            
            # Generate title for the thread
            await summarize_thread(thread_id)

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        input_messages = map_to_langchain_messages(request.messages)
        graph = await get_graph()
        
        # Configure thread_id
        thread_id = request.thread_id or str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        
        final_state = await graph.ainvoke({"messages": input_messages}, config=config)
        output_messages = map_from_langchain_messages(final_state["messages"])
        return ChatResponse(messages=output_messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
