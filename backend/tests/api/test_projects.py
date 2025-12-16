import shutil
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.display_algorithm import DisplayAlgorithm
from app.services.project import DATA_SOURCE_ROOT


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


def prepare_data_source(name: str | None = None) -> str:
    """Create a fake data source folder with dummy files."""
    folder_name = name or f"ds_{uuid4().hex[:8]}"
    folder = DATA_SOURCE_ROOT / folder_name
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "sample1.png").write_bytes(b"dummy")
    (folder / "sample2.png").write_bytes(b"dummy")
    return folder_name


def prepare_hyper_data_source(name: str | None = None) -> str:
    """Create a fake hyperspectral data source with paired files."""
    folder_name = name or f"hyper_ds_{uuid4().hex[:8]}"
    folder = DATA_SOURCE_ROOT / folder_name
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "sample1.spe").write_bytes(b"spe-bytes")
    (folder / "sample1.hdr").write_bytes(b"header")
    return folder_name


async def seed_display_algorithms(db_session: AsyncSession) -> None:
    """Insert minimal display algorithms for tests."""
    if await db_session.get(DisplayAlgorithm, 1):
        return
    db_session.add_all(
        [
            DisplayAlgorithm(code="linear", name="Linear", description="Linear stretch"),
            DisplayAlgorithm(code="percentile", name="Percentile", description="Percentile stretch"),
        ]
    )
    await db_session.flush()


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient) -> None:
    token = await get_auth_token(client, "project_create@example.com", "password123")
    folder = prepare_data_source("project_create_ds")

    response = await client.post(
        "/api/v1/projects",
        json={
            "name": "植被标注",
            "priority": "high",
            "data_source_folder": folder,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "植被标注"
    assert data["priority"] == "high"
    assert data["available_samples"] == 2
    assert data["total_samples"] == 2


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient) -> None:
    token = await get_auth_token(client, "project_list@example.com", "password123")
    for idx in range(2):
        folder = prepare_data_source(f"project_list_ds_{idx}")
        await client.post(
            "/api/v1/projects",
            json={
                "name": f"项目{idx}",
                "data_source_folder": folder,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    response = await client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient) -> None:
    token = await get_auth_token(client, "project_update@example.com", "password123")
    folder = prepare_data_source("project_update_ds")
    create_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "旧项目",
            "data_source_folder": folder,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={
            "name": "新项目",
            "priority": "high",
            "completion_rate": 50,
            "available_samples": 30,
            "total_samples": 60,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "新项目"
    assert data["priority"] == "high"
    assert data["completion_rate"] == 50


@pytest.mark.asyncio
async def test_archive_restore_project(client: AsyncClient) -> None:
    token = await get_auth_token(client, "project_archive@example.com", "password123")
    folder = prepare_data_source("project_archive_ds")
    create_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "归档测试",
            "priority": "high",
            "data_source_folder": folder,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = create_resp.json()["id"]

    archive_resp = await client.post(
        f"/api/v1/projects/{project_id}/archive",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert archive_resp.status_code == 200
    assert archive_resp.json()["is_archived"] is True
    assert archive_resp.json()["priority"] == "normal"

    restore_resp = await client.post(
        f"/api/v1/projects/{project_id}/restore",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert restore_resp.status_code == 200
    assert restore_resp.json()["is_archived"] is False


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient) -> None:
    token = await get_auth_token(client, "project_delete@example.com", "password123")
    folder = prepare_data_source("project_delete_ds")
    create_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "待删除",
            "data_source_folder": folder,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    project_id = create_resp.json()["id"]

    delete_resp = await client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_resp.status_code == 204

    get_resp = await client.get(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_export_project_annotations(client: AsyncClient, db_session: AsyncSession) -> None:
    await seed_display_algorithms(db_session)
    token = await get_auth_token(client, "project_export@example.com", "password123")
    folder = prepare_hyper_data_source("project_export_ds")

    create_resp = await client.post(
        "/api/v1/projects",
        json={
            "name": "人脸光谱",
            "priority": "normal",
            "data_source_folder": folder,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201
    project_id = create_resp.json()["id"]

    samples_resp = await client.get(
        f"/api/v1/projects/{project_id}/samples",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert samples_resp.status_code == 200
    sample_items = samples_resp.json()["items"]
    assert len(sample_items) == 1
    assert sample_items[0]["sample_type"] == "hyperspectral"

    first_sample_id = sample_items[0]["id"]
    annotate_resp = await client.put(
        f"/api/v1/samples/{first_sample_id}/annotations",
        json={
            "annotations": [
                {
                    "label_name": "鼻子",
                    "color": "#ff0000",
                    "tool_type": "rect",
                    "coordinates": {"x": 10, "y": 20, "width": 30, "height": 40},
                    "mode_snapshot": {
                        "r_channel": 0,
                        "g_channel": 1,
                        "b_channel": 2,
                        "r_gain": 1.0,
                        "g_gain": 1.0,
                        "b_gain": 1.0,
                        "gain_algorithm": "linear",
                        "dark_calibration": False,
                        "white_calibration": False,
                    },
                    "spectra": [
                        {
                            "position": {"x": 15, "y": 25},
                            "points": [
                                {"wavelength": 450, "intensity": 0.1},
                                {"wavelength": 550, "intensity": 0.8},
                            ],
                        }
                    ],
                }
            ],
            "mark_annotated": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert annotate_resp.status_code == 200

    export_resp = await client.post(
        f"/api/v1/projects/{project_id}/export",
        json={
            "include_project_meta": True,
            "include_sample_meta": True,
            "include_annotation_bundle": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert export_resp.status_code == 200
    data = export_resp.json()

    assert data["included_sections"]["project_meta"] is True
    assert len(data["samples"]) == len(sample_items)
    first_block = data["samples"][0]
    assert first_block["sample_id"] == sample_items[0]["sample_id"]
    assert first_block["meta"]["sample_type"] == "hyperspectral"
    annotations = first_block["annotations"]
    assert annotations is not None
    assert len(annotations) == 1
    detail = annotations[0]["detail"]
    assert detail["label_name"] == "鼻子"
    assert annotations[0]["mode_snapshot"]["r_channel"] == 0
    assert len(annotations[0]["spectra"]) == 1
