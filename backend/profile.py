import aiosqlite
import json
from langchain_core.tools import tool

DB_PATH = "checkpoints.db"

async def ensure_profile_table():
    async with aiosqlite.connect(DB_PATH) as db:
        # Table for general profile info (goals)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                id TEXT PRIMARY KEY,
                learning_goals TEXT,
                self_description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Table for categorized knowledge
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_knowledge (
                category TEXT PRIMARY KEY,
                content TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def get_user_profile():
    async with aiosqlite.connect(DB_PATH) as db:
        # Get goals and description
        goals = "尚无学习目标。"
        description = "尚无自我描述。"
        
        # Check if column exists (for migration)
        try:
            async with db.execute("SELECT learning_goals, self_description FROM user_profile WHERE id = 'global'") as cursor:
                row = await cursor.fetchone()
                if row:
                    goals = row[0] or goals
                    description = row[1] or description
        except aiosqlite.OperationalError:
            # Fallback if column missing, or run migration
            # For simplicity, we just fetch goals if description column missing
             async with db.execute("SELECT learning_goals FROM user_profile WHERE id = 'global'") as cursor:
                row = await cursor.fetchone()
                if row:
                    goals = row[0] or goals
        
        # Get knowledge categories
        knowledge = {}
        async with db.execute("SELECT category, content FROM user_knowledge") as cursor:
            rows = await cursor.fetchall()
            for r in rows:
                knowledge[r[0]] = r[1]
        
        return {
            "learning_goals": goals,
            "self_description": description,
            "knowledge": knowledge
        }

async def clear_user_profile():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM user_profile WHERE id = 'global'")
        await db.execute("DELETE FROM user_knowledge")
        await db.commit()
    return {"message": "User profile cleared successfully"}

async def set_knowledge_category(category: str, content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO user_knowledge (category, content, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(category) DO UPDATE SET
                content = excluded.content,
                updated_at = CURRENT_TIMESTAMP
        """, (category, content))
        await db.commit()

async def set_learning_goals(goals: str):
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if column exists, if not add it
        try:
            await db.execute("SELECT self_description FROM user_profile LIMIT 1")
        except aiosqlite.OperationalError:
            await db.execute("ALTER TABLE user_profile ADD COLUMN self_description TEXT")
            await db.commit()

        await db.execute("""
            INSERT INTO user_profile (id, learning_goals, updated_at)
            VALUES ('global', ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                learning_goals = excluded.learning_goals,
                updated_at = CURRENT_TIMESTAMP
        """, (goals,))
        await db.commit()

async def set_self_description(description: str):
    async with aiosqlite.connect(DB_PATH) as db:
        # Check if column exists, if not add it
        try:
            await db.execute("SELECT self_description FROM user_profile LIMIT 1")
        except aiosqlite.OperationalError:
            await db.execute("ALTER TABLE user_profile ADD COLUMN self_description TEXT")
            await db.commit()
            
        await db.execute("""
            INSERT INTO user_profile (id, self_description, updated_at)
            VALUES ('global', ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                self_description = excluded.self_description,
                updated_at = CURRENT_TIMESTAMP
        """, (description,))
        await db.commit()

@tool
async def update_knowledge_category(category: str, content: str) -> str:
    """
    Update the user's knowledge summary for a specific category.
    This allows for granular updates without overwriting other knowledge areas.
    
    Args:
        category: The category of knowledge (e.g., 'Programming Languages', 'Algorithms', 'System Design', 'Frameworks', 'Tools').
        content: A summary of what the user knows and what they are missing in this category.
    """
    try:
        await set_knowledge_category(category, content)
        return f"Successfully updated knowledge category: {category}"
    except Exception as e:
        return f"Error updating knowledge category: {str(e)}"

@tool
async def update_learning_goals(goals: str) -> str:
    """
    Update the user's current learning goals.
    
    Args:
        goals: A text description of the user's short-term and long-term learning objectives.
    """
    try:
        await set_learning_goals(goals)
        return "Successfully updated learning goals."
    except Exception as e:
        return f"Error updating learning goals: {str(e)}"
