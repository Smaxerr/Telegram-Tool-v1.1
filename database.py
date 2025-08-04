import asyncpg
from config import DB_CONFIG

pool: asyncpg.Pool | None = None  # global pool variable

async def init_db_pool():
    global pool
    pool = await asyncpg.create_pool(**DB_CONFIG)
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT PRIMARY KEY,
                username TEXT,
                balance INTEGER DEFAULT 0,
                ovo_id TEXT
            );
        """)
        await conn.execute("""
            ALTER TABLE users
            ADD COLUMN IF NOT EXISTS ovo_id TEXT;
        """)

async def get_user(user_id):
    async with pool.acquire() as conn:
        user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return user

async def register_user(user_id, username):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (id, username)
            VALUES ($1, $2)
            ON CONFLICT (id) DO NOTHING;
        """, user_id, username)

async def get_balance(user_id):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT balance FROM users WHERE id = $1", user_id)
        return row['balance'] if row else 0

async def set_balance(user_id, amount):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET balance = $1 WHERE id = $2", amount, user_id)

async def add_balance(user_id, amount):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET balance = balance + $1 WHERE id = $2", amount, user_id)

async def get_all_users():
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT id, username, balance FROM users")

async def set_ovo_id(user_id: int, ovo_id: str):
    await db.execute(
        "UPDATE users SET ovo_id = ? WHERE user_id = ?",
        (ovo_id, user_id),
    )
    await db.commit()

async def get_ovo_id(user_id: int) -> str | None:
    row = await db.execute_fetchone(
        "SELECT ovo_id FROM users WHERE user_id = ?",
        (user_id,),
    )
    if row and row[0]:
        return row[0]
    return None
