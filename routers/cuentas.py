from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models.cuenta import Cuenta
from schemas.cuenta import CuentaCreate, CuentaOut
from dependencies import get_current_user

router = APIRouter(
    prefix="/cuentas",
    tags=["Cuentas"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=CuentaOut)
def crear_cuenta(data: CuentaCreate, user=Depends(get_current_user)):
    db: Session = SessionLocal()
    cuenta = Cuenta(usuario_id=user.id, nombre=data.nombre)
    db.add(cuenta)
    db.commit()
    db.refresh(cuenta)
    return cuenta

@router.get("/", response_model=list[CuentaOut])
def listar_cuentas(user=Depends(get_current_user)):
    db: Session = SessionLocal()
    return db.query(Cuenta).filter(Cuenta.usuario_id == user.id).all()
