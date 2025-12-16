from fastapi import APIRouter

from app.api.v1 import auth, health, label_groups, projects, samples, spectral_modes, todos, users

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(todos.router, prefix="/todos", tags=["todos"])
api_router.include_router(label_groups.router, prefix="/label-groups", tags=["label-groups"])
api_router.include_router(
    spectral_modes.router, prefix="/spectral-modes", tags=["spectral-modes"]
)
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(samples.router, tags=["samples"])
