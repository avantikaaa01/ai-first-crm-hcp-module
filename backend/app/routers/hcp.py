from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/hcps", tags=["hcps"])


@router.get("/", response_model=List[schemas.HCPOut])
def list_hcps(db: Session = Depends(get_db)):
    return db.query(models.HCP).all()


@router.post("/", response_model=schemas.HCPOut)
def create_hcp(hcp: schemas.HCPCreate, db: Session = Depends(get_db)):
    db_hcp = models.HCP(**hcp.model_dump())
    db.add(db_hcp)
    db.commit()
    db.refresh(db_hcp)
    return db_hcp


@router.get("/{hcp_id}", response_model=schemas.HCPOut)
def get_hcp(hcp_id: str, db: Session = Depends(get_db)):
    hcp = db.query(models.HCP).filter(models.HCP.id == hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail="HCP not found")
    return hcp
