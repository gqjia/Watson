from langchain_openai import ChatOpenAI
import os
import yaml
from dotenv import load_dotenv

load_dotenv()

# --- Load Prompts ---
with open(os.path.join(os.path.dirname(__file__), "prompts.yaml"), "r", encoding="utf-8") as f:
    prompts = yaml.safe_load(f)["prompts"]

COACH_DRAFT_PROMPT = prompts["coach_draft"]
CRITIC_REFLECTION_PROMPT = prompts["critic_reflection"]
COACH_FINAL_PROMPT = prompts["coach_final"]
MENTOR_PROMPT = prompts["mentor"]

# --- LLM Configuration ---
llm = ChatOpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    model="deepseek-chat", 
    temperature=0.7,
    streaming=True
)
