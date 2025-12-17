from pydantic import BaseModel

class CuentaCreate(BaseModel):
    nombre: str

class CuentaOut(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True
