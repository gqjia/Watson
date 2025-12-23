import os
import requests
import json
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

@tool
def web_search(query: str) -> str:
    """
    Perform a web search using Bocha API to get up-to-date information.
    Useful for answering questions about current events, specific technical details, or finding learning resources.
    
    Args:
        query: The search query string.
    """
    api_key = os.getenv("BOCHA_API_KEY")
    if not api_key:
        return "Error: BOCHA_API_KEY is not set in the environment variables."

    url = "https://api.bocha.cn/v1/web-search"
    
    payload = json.dumps({
        "query": query,
        "summary": True,
        "count": 5  # Limit to 5 results to keep context manageable
    })
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.request("POST", url, headers=headers, data=payload)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse and format the results
        if "data" in data and "webPages" in data["data"]:
            results = []
            for item in data["data"]["webPages"]["value"]:
                title = item.get("name", "No Title")
                url = item.get("url", "No URL")
                snippet = item.get("snippet", "")
                summary = item.get("summary", "")
                results.append(f"Title: {title}\nURL: {url}\nSnippet: {snippet}\nSummary: {summary}\n")
            
            return "\n---\n".join(results) if results else "No results found."
        else:
            return f"No search results found. API Response: {data}"
            
    except Exception as e:
        return f"Error performing web search: {str(e)}"
