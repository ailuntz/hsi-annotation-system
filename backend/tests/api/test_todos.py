import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str, password: str) -> str:
    """Helper to register and login a user, returning the access token."""
    # Register
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    # Login
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_todo(client: AsyncClient) -> None:
    """Test creating a todo."""
    token = await get_auth_token(client, "todo_user@example.com", "password123")

    response = await client.post(
        "/api/v1/todos",
        json={
            "title": "Test Todo",
            "description": "Test description",
            "priority": 1,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["description"] == "Test description"
    assert data["priority"] == 1
    assert data["completed"] is False
    assert "id" in data


@pytest.mark.asyncio
async def test_list_todos(client: AsyncClient) -> None:
    """Test listing todos."""
    token = await get_auth_token(client, "list_user@example.com", "password123")

    # Create some todos
    for i in range(3):
        await client.post(
            "/api/v1/todos",
            json={"title": f"Todo {i}", "priority": i},
            headers={"Authorization": f"Bearer {token}"},
        )

    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["page"] == 1


@pytest.mark.asyncio
async def test_get_todo(client: AsyncClient) -> None:
    """Test getting a single todo."""
    token = await get_auth_token(client, "get_user@example.com", "password123")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Get Test Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Get the todo
    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Get Test Todo"


@pytest.mark.asyncio
async def test_get_todo_not_found(client: AsyncClient) -> None:
    """Test getting a non-existent todo."""
    token = await get_auth_token(client, "notfound_user@example.com", "password123")

    response = await client.get(
        "/api/v1/todos/99999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_todo(client: AsyncClient) -> None:
    """Test updating a todo."""
    token = await get_auth_token(client, "update_user@example.com", "password123")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Original Title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Update the todo
    response = await client.patch(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title", "priority": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["priority"] == 2


@pytest.mark.asyncio
async def test_delete_todo(client: AsyncClient) -> None:
    """Test deleting a todo."""
    token = await get_auth_token(client, "delete_user@example.com", "password123")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "To Delete"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Delete the todo
    response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    # Verify it's deleted
    get_response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_toggle_todo(client: AsyncClient) -> None:
    """Test toggling todo completed status."""
    token = await get_auth_token(client, "toggle_user@example.com", "password123")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]
    assert create_response.json()["completed"] is False

    # Toggle to completed
    response = await client.post(
        f"/api/v1/todos/{todo_id}/toggle",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["completed"] is True

    # Toggle back to not completed
    response = await client.post(
        f"/api/v1/todos/{todo_id}/toggle",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["completed"] is False


@pytest.mark.asyncio
async def test_filter_todos_by_completed(client: AsyncClient) -> None:
    """Test filtering todos by completed status."""
    token = await get_auth_token(client, "filter_user@example.com", "password123")

    # Create todos
    for i in range(3):
        await client.post(
            "/api/v1/todos",
            json={"title": f"Todo {i}"},
            headers={"Authorization": f"Bearer {token}"},
        )

    # Complete the first one
    list_response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    first_todo_id = list_response.json()["items"][0]["id"]
    await client.post(
        f"/api/v1/todos/{first_todo_id}/toggle",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Filter by completed=true
    response = await client.get(
        "/api/v1/todos?completed=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1

    # Filter by completed=false
    response = await client.get(
        "/api/v1/todos?completed=false",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 2


@pytest.mark.asyncio
async def test_todo_isolation_between_users(client: AsyncClient) -> None:
    """Test that users can only see their own todos."""
    token1 = await get_auth_token(client, "user1@example.com", "password123")
    token2 = await get_auth_token(client, "user2@example.com", "password123")

    # User1 creates a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "User1 Todo"},
        headers={"Authorization": f"Bearer {token1}"},
    )
    todo_id = create_response.json()["id"]

    # User2 should not see it
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.json()["total"] == 0

    # User2 should not be able to access it directly
    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient) -> None:
    """Test that unauthorized users cannot access todos."""
    response = await client.get("/api/v1/todos")
    assert response.status_code == 401
