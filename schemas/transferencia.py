from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TransferenciaBase(BaseModel):
    created_at: datetime | None = None
    cuenta_origen_id: int
    cuenta_destino_id: int
    monto: float
    descripcion: Optional[str] = None


class TransferenciaCreate(TransferenciaBase):
    pass


class TransferenciaUpdate(BaseModel):
    cuenta_origen_id: Optional[int] = None
    cuenta_destino_id: Optional[int] = None
    monto: Optional[float] = None
    descripcion: Optional[str] = None


class TransferenciaOut(TransferenciaBase):
    id: int
    cuenta_origen_id: int
    cuenta_destino_id: int
    monto: float
    estado: str

    class Config:
        from_attributes = True
