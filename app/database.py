"""Database connection and CRUD operations for todos."""

import aiosqlite

DATABASE_PATH = "todo.db"


async def init_db() -> None:
    """Initialize the database and create the todos table if it doesn't exist."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT 0,
                position INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()


async def get_db():
    """Async generator that yields a database connection with row_factory set."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


async def fetch_all_todos(db: aiosqlite.Connection) -> list[dict]:
    """Fetch all todos ordered by position ASC, created_at DESC."""
    cursor = await db.execute(
        "SELECT * FROM todos ORDER BY position ASC, created_at DESC"
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def create_todo(db: aiosqlite.Connection, title: str) -> dict:
    """Create a new todo with title. Position = MAX(position) + 1."""
    cursor = await db.execute(
        "INSERT INTO todos (title, position) VALUES (?, COALESCE((SELECT MAX(position) FROM todos), -1) + 1)",
        (title,),
    )
    await db.commit()
    todo_id = cursor.lastrowid
    cursor = await db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
    row = await cursor.fetchone()
    return dict(row)


async def fetch_todo_by_id(db: aiosqlite.Connection, todo_id: int) -> dict | None:
    """Fetch a single todo by ID. Returns None if not found."""
    cursor = await db.execute("SELECT * FROM todos WHERE id = ?", (todo_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_todo(
    db: aiosqlite.Connection,
    todo_id: int,
    title: str | None = None,
    completed: bool | None = None,
) -> dict | None:
    """Update a todo's title and/or completed state. Returns updated todo or None."""
    if title is not None and completed is not None:
        await db.execute(
            "UPDATE todos SET title = ?, completed = ? WHERE id = ?",
            (title, completed, todo_id),
        )
    elif title is not None:
        await db.execute(
            "UPDATE todos SET title = ? WHERE id = ?",
            (title, todo_id),
        )
    elif completed is not None:
        await db.execute(
            "UPDATE todos SET completed = ? WHERE id = ?",
            (completed, todo_id),
        )
    else:
        return None

    await db.commit()
    return await fetch_todo_by_id(db, todo_id)


async def delete_todo(db: aiosqlite.Connection, todo_id: int) -> bool:
    """Delete a todo by ID. Returns True if deleted, False if not found."""
    cursor = await db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    await db.commit()
    return cursor.rowcount > 0
