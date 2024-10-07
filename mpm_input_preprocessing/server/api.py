import logging
from logging import Logger

from fastapi import FastAPI, Response, status

from ..settings import app_settings
from .middleware import setup_middleware
from .router import api_router, tags_metadata

logger: Logger = logging.getLogger(__name__)

api = FastAPI(debug=True, openapi_tags=tags_metadata)

setup_middleware(api)

api.include_router(api_router, prefix=app_settings.api_prefix)



@api.get("/_/health", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, include_in_schema=False)
async def health():
    pass


@api.on_event("startup")
async def startup_event() -> None:
    logger.info("startup")
    logger.debug(app_settings)
    # print_debug_routes()