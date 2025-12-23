import aiosqlite
import sqlite3

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

async def delete_thread(thread_id: str):
    async with aiosqlite.connect("checkpoints.db") as db:
        # Delete from checkpoints
        await db.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
        await db.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
        # Delete from metadata
        await db.execute("DELETE FROM thread_metadata WHERE thread_id = ?", (thread_id,))
        await db.commit()
    return True

async def delete_all_threads():
    async with aiosqlite.connect("checkpoints.db") as db:
        await db.execute("DELETE FROM checkpoints")
        await db.execute("DELETE FROM writes")
        await db.execute("DELETE FROM thread_metadata")
        await db.commit()
    return True
