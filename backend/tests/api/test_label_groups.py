import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str, password: str) -> str:
    """注册并登录，返回 token。"""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_label_group(client: AsyncClient) -> None:
    token = await get_auth_token(client, "group_user@example.com", "password123")
    response = await client.post(
        "/api/v1/label-groups",
        json={
            "name": "基础标签组",
            "labels": [
                {"name": "目标", "color": "#FF0000"},
                {"name": "背景", "color": "#00FF00"},
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "基础标签组"
    assert len(data["labels"]) == 2
    assert data["labels"][0]["name"] == "目标"


@pytest.mark.asyncio
async def test_list_label_groups(client: AsyncClient) -> None:
    token = await get_auth_token(client, "list_group@example.com", "password123")
    for idx in range(2):
        await client.post(
            "/api/v1/label-groups",
            json={
                "name": f"预置组{idx}",
                "labels": [{"name": "标签", "color": "#123456"}],
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    response = await client.get(
        "/api/v1/label-groups",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_update_label_group(client: AsyncClient) -> None:
    token = await get_auth_token(client, "update_group@example.com", "password123")
    create_resp = await client.post(
        "/api/v1/label-groups",
        json={
            "name": "原始组",
            "labels": [{"name": "旧", "color": "#111111"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    group_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/label-groups/{group_id}",
        json={
            "name": "更新后",
            "labels": [
                {"name": "新1", "color": "#222222"},
                {"name": "新2", "color": "#333333"},
            ],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "更新后"
    assert len(data["labels"]) == 2
    assert data["labels"][1]["name"] == "新2"


@pytest.mark.asyncio
async def test_delete_label_group(client: AsyncClient) -> None:
    token = await get_auth_token(client, "delete_group@example.com", "password123")
    create_resp = await client.post(
        "/api/v1/label-groups",
        json={
            "name": "待删除",
            "labels": [{"name": "临时", "color": "#654321"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    group_id = create_resp.json()["id"]

    delete_resp = await client.delete(
        f"/api/v1/label-groups/{group_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_resp.status_code == 204

    get_resp = await client.get(
        f"/api/v1/label-groups/{group_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_search_label_groups(client: AsyncClient) -> None:
    token = await get_auth_token(client, "search_group@example.com", "password123")
    await client.post(
        "/api/v1/label-groups",
        json={
            "name": "光谱标签",
            "labels": [{"name": "光谱", "color": "#abcdef"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/label-groups",
        json={
            "name": "通用标签",
            "labels": [{"name": "默认", "color": "#123123"}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    response = await client.get(
        "/api/v1/label-groups",
        params={"search": "光谱"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "光谱标签"
