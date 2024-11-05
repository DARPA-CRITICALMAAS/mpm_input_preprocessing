import logging
from logging import Logger
import json
from fastapi import APIRouter, BackgroundTasks, HTTPException
from cdr_schemas.events import Event
from fastapi import Depends, Request, status
from cdr_schemas.cdr_responses.prospectivity import (
    CriticalMineralAssessment,
    CreateProcessDataLayer,
    CreateVectorProcessDataLayer,
)


import hashlib
import hmac
from fastapi.security import APIKeyHeader

from mpm_input_preprocessing.common.preprocessing import preprocess, test

from mpm_input_preprocessing.settings import app_settings

prefix = "/listener"

logger: Logger = logging.getLogger(__name__)
router = APIRouter()

file_logger = logging.getLogger("file_logger")
file_logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("error_log.log")
file_handler.setLevel(logging.ERROR)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

file_logger.addHandler(file_handler)

file_logger.error("Starting file logger.")


async def event_handler(evt: Event):
    try:
        match evt:
            case Event(event="ping"):
                logger.info("Received PING!")
            case Event(event="prospectivity_evidence_layers.process"):
                logger.info("Received preprocess event payload!")
                # logger.info(evt.payload)
                evidence_layer_objects_formated = []
                for x in evt.payload.get("evidence_layers"):
                    for i, method in enumerate(x.get("transform_methods")):
                        if "{" in method:
                            x["transform_methods"][i] = json.loads(method)

                    evidence_layer_objects_formated.append(x)

                evidence_layer_objects = [
                    CreateProcessDataLayer(**x) for x in evidence_layer_objects_formated
                ]

                feature_layer_objects = [
                    CreateVectorProcessDataLayer(**x)
                    for x in evt.payload.get("vector_layers")
                ]

                cma = CriticalMineralAssessment.model_validate(evt.payload.get("cma"))

                await preprocess(
                    cma=cma,
                    evidence_layers=evidence_layer_objects,
                    feature_layer_objects=feature_layer_objects,
                    event_id=evt.id,
                    file_logger=file_logger,
                )
            case _:
                logger.info("Nothing to do for event: %s", evt)

    except Exception:
        logger.exception("failed")
        raise


cdr_signiture = APIKeyHeader(name="x-cdr-signature-256")


async def verify_signature(
    request: Request, signature_header: str = Depends(cdr_signiture)
):
    payload_body = await request.body()
    if not signature_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="x-hub-signature-256 header is missing!",
        )

    hash_object = hmac.new(
        app_settings.registration_secret.encode("utf-8"),
        msg=payload_body,
        digestmod=hashlib.sha256,
    )
    expected_signature = hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Request signatures didn't match!",
        )

    return True


@router.post("/hook")
async def hook(
    evt: Event,
    background_tasks: BackgroundTasks,
    request: Request,
    verified_signature: bool = Depends(verify_signature),
):
    """Our main entry point for CDR calls"""

    background_tasks.add_task(event_handler, evt)
    return {"ok": "success"}


@router.post("/test")
async def test_er():
    test()
