from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from schemas.transferencia import TransferenciaCreate
from models.transferencia import Transferencia
from dependencies import get_current_user

router = APIRouter(
    prefix="/transferencias",
    tags=["Transferencias"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/")
def crear_transferencia(data: TransferenciaCreate, user=Depends(get_current_user)):
    db: Session = SessionLocal()
    t = Transferencia(
        usuario_id=user.id,
        fecha=data.fecha,
        cuenta_salida=data.cuenta_salida,
        cuenta_destino=data.cuenta_destino,
        monto=data.monto
    )
    db.add(t)
    db.commit()
    return {"ok": True}
