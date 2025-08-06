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
            ADD COLUMN IF NOT EXISTS api_token TEXT;
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
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET ovo_id = $1 WHERE id = $2",
            ovo_id,
            user_id,
        )

async def get_ovo_id(user_id: int) -> str | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT ovo_id FROM users WHERE id = $1",
            user_id,
        )
        if row and row['ovo_id']:
            return row['ovo_id']
        return None

async def set_api_token(user_id: int, token: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET api_token = $1 WHERE id = $2",
            token,
            user_id
        )

async def get_api_token(user_id: int) -> str | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT api_token FROM users WHERE id = $1",
            user_id
        )
        if row and row['api_token']:
            return row['api_token']
        return None
