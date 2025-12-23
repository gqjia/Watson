import aiosqlite
import json
from langchain_core.tools import tool

DB_PATH = "checkpoints.db"

async def ensure_profile_table():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                id TEXT PRIMARY KEY,
                knowledge_summary TEXT,
                learning_goals TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def get_user_profile():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT knowledge_summary, learning_goals FROM user_profile WHERE id = 'global'") as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    "knowledge_summary": row[0] or "",
                    "learning_goals": row[1] or ""
                }
            return {
                "knowledge_summary": "尚无用户画像。",
                "learning_goals": "尚无学习目标。"
            }

@tool
async def update_learning_profile(knowledge_summary: str, learning_goals: str) -> str:
    """
    Update the user's global knowledge profile and learning goals.
    Use this to record what the user has mastered, what they are struggling with, and their current learning direction.
    
    Args:
        knowledge_summary: A comprehensive summary of the user's current knowledge state, including strengths and weaknesses.
        learning_goals: A list of current and future learning objectives.
    """
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                INSERT INTO user_profile (id, knowledge_summary, learning_goals, updated_at)
                VALUES ('global', ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    knowledge_summary = excluded.knowledge_summary,
                    learning_goals = excluded.learning_goals,
                    updated_at = CURRENT_TIMESTAMP
            """, (knowledge_summary, learning_goals))
            await db.commit()
        return "Successfully updated user profile."
    except Exception as e:
        return f"Error updating profile: {str(e)}"
