from pydantic import BaseModel
from datetime import date
from decimal import Decimal

class TransferenciaCreate(BaseModel):
    fecha: date
    cuenta_salida: int
    cuenta_destino: int
    monto: Decimal
