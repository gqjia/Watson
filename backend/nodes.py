from langchain_core.messages import SystemMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from datetime import datetime

from state import State
from llm import llm, COACH_DRAFT_PROMPT, CRITIC_REFLECTION_PROMPT, COACH_FINAL_PROMPT, MENTOR_PROMPT
from tools import web_search
from profile import get_user_profile, update_knowledge_category, update_learning_goals

tools = [web_search, update_knowledge_category, update_learning_goals]
tool_map = {t.name: t for t in tools}

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

# --- Nodes ---

async def generate_draft(state: State, config: RunnableConfig):
    messages = state["messages"]
    
    # Get user profile
    profile = await get_user_profile()
    knowledge_str = "\n".join([f"- {k}: {v}" for k, v in profile.get('knowledge', {}).items()]) or "None"
    profile_str = f"User Description: {profile.get('self_description', 'None')}\n\nKnowledge Breakdown:\n{knowledge_str}\n\nLearning Goals: {profile['learning_goals']}"
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    context_str = f"\n\nToday's Date: {current_date}\n\nCURRENT USER PROFILE:\n{profile_str}"

    # Check for revision
    critic_feedback = state.get("critic_feedback")
    coach_draft = state.get("coach_draft")
    revision_count = state.get("revision_count", 0)
    
    if revision_count > 0 and critic_feedback and "PASS" not in critic_feedback:
        # Revision mode
        sys_msg = SystemMessage(content=COACH_DRAFT_PROMPT + f"{context_str}\n\nPREVIOUS DRAFT:\n{coach_draft}\n\nCRITIC FEEDBACK:\n{critic_feedback}\n\nPlease revise the draft based on the feedback.")
    else:
        # Fresh mode
        sys_msg = SystemMessage(content=COACH_DRAFT_PROMPT + context_str)
    
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
    knowledge_str = "\n".join([f"- {k}: {v}" for k, v in profile.get('knowledge', {}).items()]) or "None"
    profile_str = f"User Description: {profile.get('self_description', 'None')}\n\nKnowledge Breakdown:\n{knowledge_str}\n\nLearning Goals: {profile['learning_goals']}"
    
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
    
    # Get user profile to ensure final response also considers it
    profile = await get_user_profile()
    knowledge_str = "\n".join([f"- {k}: {v}" for k, v in profile.get('knowledge', {}).items()]) or "None"
    profile_str = f"User Description: {profile.get('self_description', 'None')}\n\nKnowledge Breakdown:\n{knowledge_str}\n\nLearning Goals: {profile['learning_goals']}"
    
    # We always want to stream the final response, even if it's just the draft.
    # So we use the LLM to output the final content.
    
    if "PASS" in feedback:
        instruction = "The critic had no complaints (PASS). Please output the draft exactly as is, without any additional commentary."
    else:
        instruction = f"The critic provided this feedback: {feedback}. Please revise the draft to address it."

    final_prompt = f"""你是“Watson”，一位友好且乐于助人的技术学习助手。

你之前生成的回复草稿收到了一些反馈意见。
{instruction}

草稿内容：
{draft}

当前用户画像：
{profile_str}

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
    knowledge_str = "\n".join([f"- {k}: {v}" for k, v in profile.get('knowledge', {}).items()]) or "None"
    profile_str = f"User Description: {profile.get('self_description', 'None')}\n\nKnowledge Breakdown:\n{knowledge_str}\n\nLearning Goals: {profile['learning_goals']}"
    
    current_date = datetime.now().strftime("%Y-%m-%d")
    sys_msg = SystemMessage(content=MENTOR_PROMPT + f"\n\nToday's Date: {current_date}\n\nCURRENT USER PROFILE:\n{profile_str}")
    
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
