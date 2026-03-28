import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from mind.worker import hitl_events, hitl_resolutions

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/hitl", tags=["hitl"])


class ApproveRequest(BaseModel):
    hitl_id: str


class RejectRequest(BaseModel):
    hitl_id: str


class EditRequest(BaseModel):
    hitl_id: str
    edited_value: str


@router.post("/approve")
async def approve_action(req: ApproveRequest):
    event = hitl_events.get(req.hitl_id)
    if not event:
        raise HTTPException(status_code=404, detail="HITL request not found")

    hitl_resolutions[req.hitl_id] = {"resolution": "approved"}
    event.set()
    logger.info(f"HITL {req.hitl_id} approved")
    return {"status": "approved", "hitl_id": req.hitl_id}


@router.post("/reject")
async def reject_action(req: RejectRequest):
    event = hitl_events.get(req.hitl_id)
    if not event:
        raise HTTPException(status_code=404, detail="HITL request not found")

    hitl_resolutions[req.hitl_id] = {"resolution": "rejected"}
    event.set()
    logger.info(f"HITL {req.hitl_id} rejected")
    return {"status": "rejected", "hitl_id": req.hitl_id}


@router.post("/edit")
async def edit_action(req: EditRequest):
    event = hitl_events.get(req.hitl_id)
    if not event:
        raise HTTPException(status_code=404, detail="HITL request not found")

    hitl_resolutions[req.hitl_id] = {"resolution": "edited", "edited_value": req.edited_value}
    event.set()
    logger.info(f"HITL {req.hitl_id} edited: {req.edited_value[:50]}")
    return {"status": "edited", "hitl_id": req.hitl_id}
