import asyncpg
from config import DB_CONFIG

async def init_db():
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGINT PRIMARY KEY,
            username TEXT,
            balance INTEGER DEFAULT 0
        );
    """)
    await conn.close()

async def get_user(conn, user_id):
    user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
    return user

async def register_user(conn, user_id, username):
    await conn.execute("""
        INSERT INTO users (id, username)
        VALUES ($1, $2)
        ON CONFLICT (id) DO NOTHING;
    """, user_id, username)

async def get_balance(conn, user_id):
    row = await conn.fetchrow("SELECT balance FROM users WHERE id = $1", user_id)
    return row['balance'] if row else 0

async def set_balance(conn, user_id, amount):
    await conn.execute("UPDATE users SET balance = $1 WHERE id = $2", amount, user_id)

async def add_balance(conn, user_id, amount):
    await conn.execute("UPDATE users SET balance = balance + $1 WHERE id = $2", amount, user_id)

async def get_all_users(conn):
    return await conn.fetch("SELECT id, username, balance FROM users")
