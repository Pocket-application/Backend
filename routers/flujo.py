from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models.flujo import Flujo
from schemas.flujo import FlujoCreate
from dependencies import get_current_user

router = APIRouter(
    prefix="/flujo",
    tags=["Flujo"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/")
def crear_movimiento(data: FlujoCreate, user=Depends(get_current_user)):
    db: Session = SessionLocal()
    mov = Flujo(usuario_id=user.id, **data.dict())
    db.add(mov)
    db.commit()
    return {"ok": True}

@router.get("/")
def listar_movimientos(user=Depends(get_current_user)):
    db: Session = SessionLocal()
    return db.query(Flujo).filter(
        Flujo.usuario_id == user.id
    ).order_by(Flujo.fecha.desc()).all()
