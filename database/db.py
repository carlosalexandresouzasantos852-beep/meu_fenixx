import aiosqlite
from config import DB_PATH


async def connect_db():
    return await aiosqlite.connect(DB_PATH)


async def setup_tables():
    db = await connect_db()

    await db.execute("""
        CREATE TABLE IF NOT EXISTS farm_entregas (
            user_id INTEGER,
            entregas INTEGER DEFAULT 0,
            meta INTEGER DEFAULT 100
        )
    """)

    await db.commit()
    await db.close()