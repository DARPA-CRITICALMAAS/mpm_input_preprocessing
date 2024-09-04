import logging
from logging import Logger

from fastapi import APIRouter, BackgroundTasks, HTTPException
from cdr_schemas.events import Event
from fastapi import (BackgroundTasks, Depends,HTTPException, Request,
                     status)

import hashlib
import hmac
from fastapi.security import APIKeyHeader

from common import run_ta3_pipeline

from cdr_schemas.cdr_responses.prospectivity import ProspectModelMetaData
from mpm_input_preprocessing.settings import app_settings
prefix = "/listener"

logger: Logger = logging.getLogger(__name__)
router = APIRouter()


async def event_handler(evt: Event):
    try:
        match evt:
            case Event(event="ping"):
                print("Received PING!")
            case Event(event="prospectivity_model_run.process"):
                print("Received model run event payload!")
                print(evt.payload)
                run_ta3_pipeline(
                    ProspectModelMetaData(
                        model_run_id = evt.payload.get("model_run_id"),
                        cma = evt.payload.get("cma"),
                        model_type = evt.payload.get("model_type"),
                        train_config = evt.payload.get("train_config"),
                        evidence_layers = evt.payload.get("evidence_layers"),
                        ), app_settings)
            case _:
                print("Nothing to do for event: %s", evt)

    except Exception:
        print("background processing event: %s", evt)
        raise

cdr_signiture = APIKeyHeader(name="x-cdr-signature-256")


async def verify_signature(request: Request, signature_header: str = Depends(cdr_signiture)):

    payload_body = await request.body()
    if not signature_header:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="x-hub-signature-256 header is missing!")

    hash_object = hmac.new(app_settings.registration_secret.encode(
        "utf-8"), msg=payload_body, digestmod=hashlib.sha256)
    expected_signature = hash_object.hexdigest()
    if not hmac.compare_digest(expected_signature, signature_header):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Request signatures didn't match!")

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



