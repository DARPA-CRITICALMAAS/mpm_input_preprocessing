from fastapi import APIRouter

from .routes import health, listener

tags_metadata = [
    {
        "name": "Health",
        "description": "Health Checks",
    },
    {
        "name": "Listener",
        "description": "Listen For Events",
    },
]

api_router = APIRouter()
api_router.include_router(health.router, prefix=health.prefix, tags=["Health"])
api_router.include_router(listener.router, prefix=listener.prefix, tags=["Listener"])
