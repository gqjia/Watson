from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from dotenv import load_dotenv
import os
import json
import yaml
import sqlite3
import aiosqlite
from tools import web_search
from profile import ensure_profile_table, get_user_profile, update_learning_profile

load_dotenv()

# --- Load Prompts ---
with open(os.path.join(os.path.dirname(__file__), "prompts.yaml"), "r", encoding="utf-8") as f:
    prompts = yaml.safe_load(f)["prompts"]

COACH_DRAFT_PROMPT = prompts["coach_draft"]
CRITIC_REFLECTION_PROMPT = prompts["critic_reflection"]
COACH_FINAL_PROMPT = prompts["coach_final"]
MENTOR_PROMPT = prompts["mentor"]

# --- State Definition ---
class State(TypedDict):
    messages: Annotated[list, add_messages]
    coach_draft: str
    critic_feedback: str
    mentor_advice: str
    search_results: str  # New field to store search results for frontend
    revision_count: int

# --- LLM Configuration ---
llm = ChatOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    model="deepseek-chat", 
    temperature=0.7,
    streaming=True
)

tools = [web_search, update_learning_profile]
tool_map = {t.name: t for t in tools}
# llm_with_tools = llm.bind_tools(tools) # Moved to run_with_tools

# --- Helper for Tool Loop ---
async def run_with_tools(messages, config, available_tools=None):
    if available_tools is None:
        available_tools = tools
        
    bound_llm = llm.bind_tools(available_tools)
    
    # Loop until we get a final text response (no tool calls)
    current_messages = list(messages) # Shallow copy
    all_search_results = []
    
    # Max steps to prevent infinite loops
    for _ in range(5):
        response = await bound_llm.ainvoke(current_messages, config)
        
        if not response.tool_calls:
            # If we collected search results, we might want to attach them to the response or state somehow.
            # But the caller expects just a message response.
            # We can't easily modify the response object to add arbitrary fields that LangChain/LangGraph will preserve 
            # unless we put it in the state.
            # For now, let's just return the response, and we handle state update in the calling node if possible.
            # But wait, run_with_tools is a helper, it doesn't return state dict.
            # We need to return both response and search results.
            return response, "\n\n".join(all_search_results)
            
        # Execute tools
        current_messages.append(response)
        
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            tool_instance = tool_map.get(tool_name)
            if tool_instance:
                 # Check if we need to await (async tool) or not.
                 # LangChain tools are runnables. ainvoke handles both.
                 # For web_search (sync), ainvoke runs it in threadpool.
                 # For update_learning_profile (async), ainvoke runs it directly.
                 try:
                    tool_output = await tool_instance.ainvoke(tool_args)
                 except Exception as e:
                    tool_output = f"Error executing tool {tool_name}: {str(e)}"
                 
                 # Format output for display if it's a search result
                 if tool_name == "web_search":
                     all_search_results.append(f"Query: {tool_args.get('query')}\nResult: {tool_output}")
            else:
                 tool_output = f"Error: Tool {tool_name} not found."
                
            current_messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_id))
            
    return response, "\n\n".join(all_search_results)

# --- Prompts ---
# Removed hardcoded prompts as they are now loaded from prompts.yaml

# --- Nodes ---

async def generate_draft(state: State, config: RunnableConfig):
    messages = state["messages"]
    
    # Get user profile
    profile = await get_user_profile()
    profile_str = f"Knowledge Summary: {profile['knowledge_summary']}\nLearning Goals: {profile['learning_goals']}"
    
    # Check for revision
    critic_feedback = state.get("critic_feedback")
    coach_draft = state.get("coach_draft")
    revision_count = state.get("revision_count", 0)
    
    if revision_count > 0 and critic_feedback and "PASS" not in critic_feedback:
        # Revision mode
        sys_msg = SystemMessage(content=COACH_DRAFT_PROMPT + f"\n\nCURRENT USER PROFILE:\n{profile_str}\n\nPREVIOUS DRAFT:\n{coach_draft}\n\nCRITIC FEEDBACK:\n{critic_feedback}\n\nPlease revise the draft based on the feedback.")
    else:
        # Fresh mode
        sys_msg = SystemMessage(content=COACH_DRAFT_PROMPT + f"\n\nCURRENT USER PROFILE:\n{profile_str}")
    
    # Draft generation
    # Use a different tag so we don't stream this to the user as "coach"
    config["tags"] = ["coach_draft"]
    # Use run_with_tools to handle potential search
    # Coach should only use web_search, not update_profile
    response, search_results = await run_with_tools([sys_msg] + messages, config, available_tools=[web_search])
    return {"coach_draft": response.content, "search_results": search_results}

async def critique_draft(state: State, config: RunnableConfig):
    messages = state["messages"]
    draft = state.get("coach_draft", "")
    revision_count = state.get("revision_count", 0)
    
    # Get user profile
    profile = await get_user_profile()
    profile_str = f"Knowledge Summary: {profile['knowledge_summary']}\nLearning Goals: {profile['learning_goals']}"
    
    # Format the prompt with the draft
    prompt = CRITIC_REFLECTION_PROMPT.format(coach_draft=draft)
    sys_msg = SystemMessage(content=prompt + f"\n\nCURRENT USER PROFILE:\n{profile_str}")
    
    # We pass the conversation history too, so critic knows context
    # But we append the draft as context implicitly via prompt
    config["tags"] = ["critic"]
    response = await llm.ainvoke([sys_msg] + messages, config)
    
    return {
        "critic_feedback": response.content,
        "revision_count": revision_count + 1
        # We DO NOT append the critic message to the history. 
        # It is an internal thought process passed to generate_final via state.
    }

async def generate_final(state: State, config: RunnableConfig):
    messages = state["messages"]
    feedback = state.get("critic_feedback", "")
    draft = state.get("coach_draft", "")
    
    # We always want to stream the final response, even if it's just the draft.
    # So we use the LLM to output the final content.
    
    if "PASS" in feedback:
        instruction = "The critic had no complaints (PASS). Please output the draft exactly as is, without any additional commentary."
    else:
        instruction = f"The critic provided this feedback: {feedback}. Please revise the draft to address it."

    # Use final_prompt directly instead of COACH_FINAL_PROMPT + formatting
    # Or update COACH_FINAL_PROMPT to accept instruction. 
    # Since we construct final_prompt below manually, we don't strictly need to format COACH_FINAL_PROMPT here if we don't use it.
    # But for consistency, let's keep using final_prompt which we construct.

    final_prompt = f"""你是“Watson”，一位友好且乐于助人的技术学习助手。

你之前生成的回复草稿收到了一些反馈意见。
{instruction}

草稿内容：
{draft}

请生成最终的回复。
保持温暖、鼓励的语气。
**必须全程使用中文。**
"""
    
    config["tags"] = ["coach"]
    response = await llm.ainvoke([SystemMessage(content=final_prompt)] + messages, config)
    return {"messages": [AIMessage(content=response.content, name="coach")]}

async def mentor(state: State, config: RunnableConfig):
    messages = state["messages"]
    
    # Get user profile
    profile = await get_user_profile()
    profile_str = f"Knowledge Summary: {profile['knowledge_summary']}\nLearning Goals: {profile['learning_goals']}"
    
    sys_msg = SystemMessage(content=MENTOR_PROMPT + f"\n\nCURRENT USER PROFILE:\n{profile_str}")
    
    # The mentor sees history + final coach response
    config["tags"] = ["mentor"]
    
    # Use run_with_tools to handle potential search for resources
    # Mentor should use both web_search and update_learning_profile
    response, search_results = await run_with_tools([sys_msg] + messages, config)
    
    # We append new search results to existing ones if any?
    # Or maybe we just overwrite? The user probably wants to see relevant search results for the current turn.
    # Since search_results is a string, we can append.
    existing_search = state.get("search_results", "")
    new_search = f"{existing_search}\n\n{search_results}" if existing_search and search_results else (search_results or existing_search)
    
    # Clear revision state for next turn
    return {
        "mentor_advice": response.content, 
        "search_results": new_search,
        "revision_count": 0,
        "critic_feedback": "",
        "coach_draft": ""
    }

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

from contextlib import asynccontextmanager

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

async def ensure_metadata_table():
    async with aiosqlite.connect("checkpoints.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS thread_metadata (
                thread_id TEXT PRIMARY KEY,
                title TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def save_thread_title(thread_id: str, title: str):
    async with aiosqlite.connect("checkpoints.db") as db:
        await db.execute("""
            INSERT INTO thread_metadata (thread_id, title, updated_at) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(thread_id) DO UPDATE SET
                title = excluded.title,
                updated_at = CURRENT_TIMESTAMP
        """, (thread_id, title))
        await db.commit()

async def get_all_threads():
    async with aiosqlite.connect("checkpoints.db") as db:
        try:
            # Join checkpoints with metadata to get title and sorted by latest activity
            # If no title exists, we can return "New Chat" or null
            # We use LEFT JOIN to include threads that might not have metadata yet (though we try to create it)
            # We prioritize updated_at from metadata, but fallback to checkpoint max(checkpoint_id) order
            
            # Since getting max(checkpoint_id) is expensive for sorting, using metadata.updated_at is better if available.
            # But let's stick to existing logic for ordering if possible, or mix them.
            
            # Let's rely on metadata for the list if we ensure it's updated.
            # But initially existing threads won't have metadata.
            
            # Hybrid query:
            # Get all thread_ids from checkpoints
            # Join with metadata
            
            query = """
            SELECT c.thread_id, m.title, m.updated_at
            FROM (
                SELECT thread_id, MAX(checkpoint_id) as last_checkpoint
                FROM checkpoints
                GROUP BY thread_id
            ) c
            LEFT JOIN thread_metadata m ON c.thread_id = m.thread_id
            ORDER BY m.updated_at DESC, c.last_checkpoint DESC
            """
            
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                # Return list of dicts
                return [
                    {
                        "id": row[0],
                        "title": row[1] or "New Chat",
                        "updated_at": row[2]
                    } 
                    for row in rows
                ]
        except sqlite3.OperationalError as e:
            # Handle case where table doesn't exist yet
            if "no such table" in str(e):
                return []
            raise

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
