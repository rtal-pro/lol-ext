from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.api_v1.endpoints.champions import router as champion_router
from app.api.api_v1.endpoints.items import router as item_router
from app.api.api_v1.endpoints.runes import router as rune_router
from app.api.api_v1.endpoints.sync import router as sync_router
from app.api.api_v1.endpoints.scheduler import router as scheduler_router
from app.api.api_v1.endpoints.validation import router as validation_router
from app.api.api_v1.endpoints.assets import router as assets_router

# Main router for API v1
api_router = APIRouter()

# Include routers from different modules
api_router.include_router(health_router)

# Game data routers
api_router.include_router(champion_router, prefix="/champions")
api_router.include_router(item_router, prefix="/items")
api_router.include_router(rune_router, prefix="/runes")
api_router.include_router(sync_router, prefix="/sync")
api_router.include_router(scheduler_router, prefix="/scheduler")
api_router.include_router(validation_router, prefix="/validation")
api_router.include_router(assets_router, prefix="/assets")