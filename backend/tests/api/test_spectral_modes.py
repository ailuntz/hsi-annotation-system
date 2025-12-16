import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str, password: str) -> str:
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    return response.json()["access_token"]


def sample_payload(name: str = "默认模式") -> dict:
    return {
        "name": name,
        "r_channel": 10,
        "g_channel": 20,
        "b_channel": 30,
        "r_gain": 1.0,
        "g_gain": 1.2,
        "b_gain": 0.8,
        "gain_algorithm": "linear",
        "dark_calibration": True,
        "white_calibration": False,
    }


@pytest.mark.asyncio
async def test_create_mode(client: AsyncClient) -> None:
    token = await get_auth_token(client, "mode_user@example.com", "password123")
    response = await client.post(
        "/api/v1/spectral-modes",
        json=sample_payload(),
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "默认模式"
    assert data["dark_calibration"] is True


@pytest.mark.asyncio
async def test_list_modes(client: AsyncClient) -> None:
    token = await get_auth_token(client, "mode_list@example.com", "password123")
    for idx in range(2):
        await client.post(
            "/api/v1/spectral-modes",
            json=sample_payload(name=f"模式{idx}"),
            headers={"Authorization": f"Bearer {token}"},
        )

    response = await client.get(
        "/api/v1/spectral-modes",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_update_mode(client: AsyncClient) -> None:
    token = await get_auth_token(client, "mode_update@example.com", "password123")
    create_resp = await client.post(
        "/api/v1/spectral-modes",
        json=sample_payload(name="旧模式"),
        headers={"Authorization": f"Bearer {token}"},
    )
    mode_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/spectral-modes/{mode_id}",
        json={"name": "新模式", "gain_algorithm": "gamma"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "新模式"
    assert data["gain_algorithm"] == "gamma"


@pytest.mark.asyncio
async def test_delete_mode(client: AsyncClient) -> None:
    token = await get_auth_token(client, "mode_delete@example.com", "password123")
    create_resp = await client.post(
        "/api/v1/spectral-modes",
        json=sample_payload(name="待删除"),
        headers={"Authorization": f"Bearer {token}"},
    )
    mode_id = create_resp.json()["id"]

    delete_resp = await client.delete(
        f"/api/v1/spectral-modes/{mode_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_resp.status_code == 204

    get_resp = await client.get(
        f"/api/v1/spectral-modes/{mode_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_search_modes(client: AsyncClient) -> None:
    token = await get_auth_token(client, "mode_search@example.com", "password123")
    await client.post(
        "/api/v1/spectral-modes",
        json=sample_payload(name="光谱模式"),
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/spectral-modes",
        json=sample_payload(name="普通模式"),
        headers={"Authorization": f"Bearer {token}"},
    )

    response = await client.get(
        "/api/v1/spectral-modes",
        params={"search": "光谱"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "光谱模式"


@pytest.mark.asyncio
async def test_gain_range_validation(client: AsyncClient) -> None:
    token = await get_auth_token(client, "mode_invalid_gain@example.com", "password123")
    response = await client.post(
        "/api/v1/spectral-modes",
        json={
            **sample_payload(name="非法增益"),
            "r_gain": 5000,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
