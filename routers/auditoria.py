from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import SessionLocal
from models.auditoria import Auditoria
from schemas.auditoria import AuditoriaResponse
from dependencies import get_db, get_current_admin

router = APIRouter(prefix="/auditoria", tags=["Auditoria"])

@router.get("/", response_model=List[AuditoriaResponse])
def get_auditoria(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Obtiene el registro de auditoría. Solo para administradores.
    """
    return db.query(Auditoria).offset(skip).limit(limit).all()

@router.get("/{id}", response_model=AuditoriaResponse)
def get_auditoria_id(
    id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """
    Obtiene un registro de auditoría por ID. Solo para administradores.
    """
    log = db.query(Auditoria).filter(Auditoria.id == id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    return log
