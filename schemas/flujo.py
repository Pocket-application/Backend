from pydantic import BaseModel
from datetime import date
from decimal import Decimal

class FlujoCreate(BaseModel):
    fecha: date
    descripcion: str | None = None
    categoria_id: int
    cuenta_id: int
    tipo_movimiento: str
    estado: str
    monto: Decimal
