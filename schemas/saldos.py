from pydantic import BaseModel
from decimal import Decimal

class SaldoCuentaOut(BaseModel):
    cuenta: str
    saldo: Decimal
