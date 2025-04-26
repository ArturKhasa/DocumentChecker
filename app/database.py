import aiosqlite
import json
import os

DB_PATH = "sessions.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                user_id INTEGER PRIMARY KEY,
                messages TEXT
            )
        """)
        await db.commit()

async def get_user_session(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT messages FROM sessions WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return json.loads(row[0])
            else:
                return []

async def save_user_session(user_id: int, messages: list[dict]):
    async with aiosqlite.connect(DB_PATH) as db:
        messages_json = json.dumps(messages)
        await db.execute(
            "INSERT INTO sessions (user_id, messages) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET messages=excluded.messages",
            (user_id, messages_json)
        )
        await db.commit()

async def reset_user_session(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
        await db.commit()