"""Model registry CRUD endpoints."""
from __future__ import annotations
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models.orm import ModelRegistry
from backend.schemas.schemas import ModelCreate, ModelOut, ModelUpdate

router = APIRouter(prefix="/models", tags=["Models"])


@router.post("/", response_model=ModelOut, status_code=status.HTTP_201_CREATED)
def create_model(payload: ModelCreate, db: Session = Depends(get_db)):
    existing = db.query(ModelRegistry).filter(ModelRegistry.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Model '{payload.name}' already exists.")
    model = ModelRegistry(id=str(uuid.uuid4()), **payload.model_dump())
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


@router.get("/", response_model=list[ModelOut])
def list_models(active_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(ModelRegistry)
    if active_only:
        q = q.filter(ModelRegistry.is_active == True)
    return q.order_by(ModelRegistry.created_at.desc()).all()


@router.get("/{model_id}", response_model=ModelOut)
def get_model(model_id: str, db: Session = Depends(get_db)):
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found.")
    return model


@router.patch("/{model_id}", response_model=ModelOut)
def update_model(model_id: str, payload: ModelUpdate, db: Session = Depends(get_db)):
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found.")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(model, k, v)
    model.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(model)
    return model


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(model_id: str, db: Session = Depends(get_db)):
    model = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found.")
    db.delete(model)
    db.commit()
