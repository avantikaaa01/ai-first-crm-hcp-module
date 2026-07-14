import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db
from ..agent.tools import build_tools

router = APIRouter(prefix="/api/interactions", tags=["interactions"])


def _get_tool(db: Session, name: str):
    tools = build_tools(db)
    return next(t for t in tools if t.name == name)


@router.get("/", response_model=List[schemas.InteractionOut])
def list_interactions(hcp_id: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Interaction)
    if hcp_id:
        q = q.filter(models.Interaction.hcp_id == hcp_id)
    return q.order_by(models.Interaction.date.desc()).all()


@router.post("/form", response_model=schemas.InteractionOut)
def create_interaction_form(payload: schemas.InteractionCreateForm, db: Session = Depends(get_db)):
    """
    Structured-form path. Still routes through the same log_interaction tool
    the chat agent uses, so both entry points (form + chat) produce identically
    shaped, LLM-summarized records - one source of truth.
    """
    tool = _get_tool(db, "log_interaction")
    result = json.loads(tool.func(
        hcp_id=payload.hcp_id,
        raw_notes=payload.notes,
        interaction_type=payload.interaction_type,
        channel="form",
    ))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    interaction = db.query(models.Interaction).filter(models.Interaction.id == result["interaction_id"]).first()
    return interaction


@router.patch("/{interaction_id}", response_model=schemas.InteractionOut)
def edit_interaction_route(interaction_id: str, payload: schemas.InteractionUpdate, db: Session = Depends(get_db)):
    tool = _get_tool(db, "edit_interaction")
    changes = {k: v for k, v in payload.model_dump().items() if v is not None}
    result = json.loads(tool.func(interaction_id=interaction_id, changes=changes))
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    return interaction


@router.get("/{interaction_id}", response_model=schemas.InteractionOut)
def get_interaction(interaction_id: str, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction
