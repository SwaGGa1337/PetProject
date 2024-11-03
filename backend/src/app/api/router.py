from fastapi import APIRouter
from src.app_config.config_api import settings

from .v1.auth import router as auth_v1
from .v1.user import router as user_v1

router = APIRouter(prefix=settings.APP_PREFIX)

router.include_router(auth_v1)
router.include_router(user_v1)