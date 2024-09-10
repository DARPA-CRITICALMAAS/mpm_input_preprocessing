import logging
from logging import Logger

from fastapi import APIRouter, Request, Response
from starlette.status import HTTP_204_NO_CONTENT

logger: Logger = logging.getLogger(__name__)

prefix = "/health"

router = APIRouter()


@router.get(
    "/check",
    summary="health check",
    description="Health check end point",
    status_code=HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def get_health_check():
    pass


@router.get(
    "/debug",
    summary="debug check",
    description="debug check",
    status_code=HTTP_204_NO_CONTENT,
    response_class=Response,
    include_in_schema=False,
)
async def get_debug_check(request: Request):
    logger.debug(request.headers)
