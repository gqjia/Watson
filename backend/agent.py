from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import SystemMessage
import aiosqlite
from dotenv import load_dotenv

from state import State
from nodes import generate_draft, critique_draft, generate_final, mentor
from store import ensure_metadata_table, save_thread_title, get_all_threads, delete_thread, delete_all_threads
from profile import ensure_profile_table
from llm import llm

load_dotenv()

# --- Graph Construction ---

def should_continue(state: State):
    feedback = state.get("critic_feedback", "")
    revision_count = state.get("revision_count", 0)
    
    if "PASS" in feedback or revision_count >= 3:
        return "generate_final"
    return "generate_draft"

builder = StateGraph(State)

# Nodes
builder.add_node("generate_draft", generate_draft)
builder.add_node("critique_draft", critique_draft)
builder.add_node("generate_final", generate_final)
builder.add_node("mentor", mentor)

# Edges
builder.add_edge(START, "generate_draft")
builder.add_edge("generate_draft", "critique_draft")
builder.add_conditional_edges(
    "critique_draft",
    should_continue,
    {
        "generate_final": "generate_final",
        "generate_draft": "generate_draft"
    }
)
builder.add_edge("generate_final", "mentor")
builder.add_edge("mentor", END)

# AsyncSqliteSaver from langgraph.checkpoint.sqlite.aio expects an initialized aiosqlite connection
# We use from_conn_string to manage connection properly

# We export builder and a function to initialize the graph with checkpointer
compiled_graph = None
saver_context = None

async def get_graph():
    global compiled_graph, saver_context
    if compiled_graph is None:
        # Ensure metadata table exists
        await ensure_metadata_table()
        # Ensure profile table exists
        await ensure_profile_table()
        
        # Use from_conn_string to manage connection properly
        saver_context = AsyncSqliteSaver.from_conn_string("checkpoints.db")
        memory = await saver_context.__aenter__()
        compiled_graph = builder.compile(checkpointer=memory)
    return compiled_graph

async def cleanup_graph():
    global saver_context
    if saver_context:
        await saver_context.__aexit__(None, None, None)

async def summarize_thread(thread_id: str):
    # Retrieve messages
    graph = await get_graph()
    state = await graph.aget_state({"configurable": {"thread_id": thread_id}})
    if not state.values or "messages" not in state.values:
        return
        
    messages = state.values["messages"]
    if not messages:
        return
        
    # Format messages for summarization
    # We take the last few exchanges or all of them?
    # For a title, the first few messages or the general topic is usually enough.
    # But if the topic changes, we want the LATEST topic.
    # The user said "Every Q&A update", so it should reflect the current state.
    # Let's feed the whole history (truncated if too long) to the LLM.
    
    # Simple text representation
    history_text = "\n".join([f"{m.type}: {m.content}" for m in messages[-10:]]) # last 10 messages
    
    prompt = f"""
    请根据以下对话内容，生成一个简短的标题（不超过 10 个字）。
    如果是中文对话，请使用中文标题。
    不要包含“标题：”等前缀，直接输出标题内容。
    
    对话内容：
    {history_text}
    """
    
    try:
        # Use a separate invocation to avoid messing with the graph state
        response = await llm.ainvoke([SystemMessage(content=prompt)])
        title = response.content.strip().replace('"', '').replace("'", "")
        await save_thread_title(thread_id, title)
    except Exception as e:
        print(f"Error generating title: {e}")
