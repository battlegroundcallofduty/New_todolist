"""Database connection and CRUD operations for todos and categories."""

import aiosqlite

DATABASE_PATH = "todo.db"

_UNSET = object()


async def init_db() -> None:
    """Initialize the database and create tables if they don't exist."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                position INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed BOOLEAN NOT NULL DEFAULT 0,
                position INTEGER NOT NULL DEFAULT 0,
                due_date TEXT,
                category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Migrate existing todos table (no-op if columns already exist)
        for col_sql in (
            "ALTER TABLE todos ADD COLUMN due_date TEXT",
            "ALTER TABLE todos ADD COLUMN category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL",
        ):
            try:
                await db.execute(col_sql)
            except Exception:
                pass
        await db.commit()


async def get_db():
    """Async generator that yields a database connection with row_factory set."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        db.row_factory = aiosqlite.Row
        yield db


# ─── Todo CRUD ────────────────────────────────────────────────

async def fetch_all_todos(db: aiosqlite.Connection) -> list[dict]:
    """Fetch all todos: incomplete first, then completed, ordered by position."""
    cursor = await db.execute(
        "SELECT * FROM todos ORDER BY completed ASC, position ASC, created_at DESC"
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def create_todo(
    db: aiosqlite.Connection,
    title: str,
    due_date: str | None = None,
    category_id: int | None = None,
) -> dict:
    """Create a new todo with title. Position = MAX(position) + 1."""
    cursor = await db.execute(
        """INSERT INTO todos (title, position, due_date, category_id)
           VALUES (?, COALESCE((SELECT MAX(position) FROM todos), -1) + 1, ?, ?)""",
        (title, due_date, category_id),
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
    title: str | None = _UNSET,
    completed: bool | None = _UNSET,
    due_date: str | None = _UNSET,
    category_id: int | None = _UNSET,
) -> dict | None:
    """Update a todo's fields. Returns updated todo or None if nothing to update."""
    col_names = []
    values = []
    for col, val in (("title", title), ("completed", completed), ("due_date", due_date), ("category_id", category_id)):
        if val is not _UNSET:
            col_names.append(col + " = ?")
            values.append(val)

    if not col_names:
        return None

    values.append(todo_id)
    await db.execute(
        "UPDATE todos SET " + ", ".join(col_names) + " WHERE id = ?",
        values,
    )
    await db.commit()
    return await fetch_todo_by_id(db, todo_id)


async def delete_todo(db: aiosqlite.Connection, todo_id: int) -> bool:
    """Delete a todo by ID. Returns True if deleted, False if not found."""
    cursor = await db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    await db.commit()
    return cursor.rowcount > 0


# ─── Category CRUD ────────────────────────────────────────────

async def fetch_all_categories(db: aiosqlite.Connection) -> list[dict]:
    """Fetch all categories ordered by position ASC."""
    cursor = await db.execute(
        "SELECT * FROM categories ORDER BY position ASC, created_at ASC"
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]


async def create_category(db: aiosqlite.Connection, name: str) -> dict:
    """Create a new category. Position = MAX(position) + 1."""
    cursor = await db.execute(
        "INSERT INTO categories (name, position) VALUES (?, COALESCE((SELECT MAX(position) FROM categories), -1) + 1)",
        (name,),
    )
    await db.commit()
    cat_id = cursor.lastrowid
    cursor = await db.execute("SELECT * FROM categories WHERE id = ?", (cat_id,))
    row = await cursor.fetchone()
    return dict(row)


async def fetch_category_by_id(db: aiosqlite.Connection, cat_id: int) -> dict | None:
    """Fetch a single category by ID. Returns None if not found."""
    cursor = await db.execute("SELECT * FROM categories WHERE id = ?", (cat_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def update_category(
    db: aiosqlite.Connection, cat_id: int, name: str
) -> dict | None:
    """Update a category's name. Returns updated category or None."""
    await db.execute("UPDATE categories SET name = ? WHERE id = ?", (name, cat_id))
    await db.commit()
    return await fetch_category_by_id(db, cat_id)


async def delete_category(db: aiosqlite.Connection, cat_id: int) -> bool:
    """Delete a category by ID. Returns True if deleted, False if not found."""
    cursor = await db.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    await db.commit()
    return cursor.rowcount > 0
