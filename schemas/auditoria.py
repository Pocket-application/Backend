from datetime import datetime
from typing import Optional
from pydantic import BaseModel, IPvAnyAddress, Json

class AuditoriaResponse(BaseModel):
    id: int
    usuario_id: Optional[str] = None
    metodo: str
    ruta: str
    status_code: int
    ip: Optional[IPvAnyAddress] = None
    body: Optional[Json] = None
    error: Optional[str] = None
    duracion_ms: int
    firma: str
    firma_anterior: Optional[str] = None
    fecha: datetime

    class Config:
        from_attributes = True
