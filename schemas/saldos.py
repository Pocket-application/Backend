from pydantic import BaseModel, Field
from decimal import Decimal

class SaldoCuentaOut(BaseModel):
    cuenta_id: int
    cuenta: str
    saldo: Decimal

class ReajusteSaldoIn(BaseModel):
    cuenta_id: int 
    saldo_real: Decimal
    descripcion: str | None = Field(default="Reajuste de saldo")