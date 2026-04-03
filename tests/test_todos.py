"""API tests for todo operations."""

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import app.database as db_module
from app.database import init_db
from app.main import app


@pytest_asyncio.fixture(autouse=True)
async def setup_db(tmp_path):
    """Isolate each test with its own temporary database."""
    test_db_path = str(tmp_path / "test.db")
    db_module.DATABASE_PATH = test_db_path
    await init_db()
    yield
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest_asyncio.fixture
async def client():
    """AsyncClient with ASGI transport for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_list_todos_empty(client):
    """GET /api/todos/ returns 200 and empty list when no todos exist."""
    res = await client.get("/api/todos/")
    assert res.status_code == 200
    assert res.json() == []


async def test_list_todos_with_items(client):
    """GET /api/todos/ returns all created todos."""
    await client.post("/api/todos/", json={"title": "첫 번째"})
    await client.post("/api/todos/", json={"title": "두 번째"})
    res = await client.get("/api/todos/")
    assert res.status_code == 200
    assert len(res.json()) == 2


async def test_create_todo_success(client):
    """POST /api/todos/ returns 201 and the created todo."""
    res = await client.post("/api/todos/", json={"title": "테스트 할 일"})
    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "테스트 할 일"
    assert body["completed"] is False
    assert "id" in body
    assert "position" in body
    assert "created_at" in body


async def test_create_todo_empty_title(client):
    """POST /api/todos/ returns 422 when title is empty string."""
    res = await client.post("/api/todos/", json={"title": ""})
    assert res.status_code == 422


async def test_create_todo_whitespace(client):
    """POST /api/todos/ returns 422 when title is whitespace-only."""
    res = await client.post("/api/todos/", json={"title": "   "})
    assert res.status_code == 422


async def test_create_todo_strips_whitespace(client):
    """POST /api/todos/ strips leading/trailing whitespace from title."""
    res = await client.post("/api/todos/", json={"title": "  할 일  "})
    assert res.status_code == 201
    assert res.json()["title"] == "할 일"


async def test_toggle_todo_complete(client):
    """PATCH /api/todos/{id} marks todo as completed."""
    create = await client.post("/api/todos/", json={"title": "완료할 일"})
    todo_id = create.json()["id"]

    res = await client.patch(f"/api/todos/{todo_id}", json={"completed": True})
    assert res.status_code == 200
    assert res.json()["completed"] is True


async def test_toggle_todo_incomplete(client):
    """PATCH /api/todos/{id} marks todo back to incomplete."""
    create = await client.post("/api/todos/", json={"title": "완료 후 되돌리기"})
    todo_id = create.json()["id"]
    await client.patch(f"/api/todos/{todo_id}", json={"completed": True})

    res = await client.patch(f"/api/todos/{todo_id}", json={"completed": False})
    assert res.status_code == 200
    assert res.json()["completed"] is False


async def test_update_todo_title(client):
    """PATCH /api/todos/{id} updates the title."""
    create = await client.post("/api/todos/", json={"title": "원래 제목"})
    todo_id = create.json()["id"]

    res = await client.patch(f"/api/todos/{todo_id}", json={"title": "새 제목"})
    assert res.status_code == 200
    assert res.json()["title"] == "새 제목"


async def test_update_todo_empty_title(client):
    """PATCH /api/todos/{id} returns 422 when updated title is empty."""
    create = await client.post("/api/todos/", json={"title": "수정 테스트"})
    todo_id = create.json()["id"]

    res = await client.patch(f"/api/todos/{todo_id}", json={"title": "   "})
    assert res.status_code == 422


async def test_update_todo_not_found(client):
    """PATCH /api/todos/{id} returns 404 for non-existent todo."""
    res = await client.patch("/api/todos/99999", json={"completed": True})
    assert res.status_code == 404


async def test_update_todo_no_fields(client):
    """PATCH /api/todos/{id} returns 400 when neither title nor completed provided."""
    create = await client.post("/api/todos/", json={"title": "필드 없음 테스트"})
    todo_id = create.json()["id"]

    res = await client.patch(f"/api/todos/{todo_id}", json={})
    assert res.status_code == 400


async def test_delete_todo_success(client):
    """DELETE /api/todos/{id} returns 204 and removes the todo."""
    create = await client.post("/api/todos/", json={"title": "삭제할 일"})
    todo_id = create.json()["id"]

    res = await client.delete(f"/api/todos/{todo_id}")
    assert res.status_code == 204

    list_res = await client.get("/api/todos/")
    assert list_res.json() == []


async def test_delete_todo_not_found(client):
    """DELETE /api/todos/{id} returns 404 for non-existent todo."""
    res = await client.delete("/api/todos/99999")
    assert res.status_code == 404
