from pydantic import BaseModel
from decimal import Decimal

class SaldoCuentaOut(BaseModel):
    cuenta_id: int
    cuenta: str
    saldo: Decimal
