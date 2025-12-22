from pydantic import BaseModel


class CuentaBase(BaseModel):
    nombre: str


class CuentaCreate(CuentaBase):
    pass


class CuentaUpdate(BaseModel):
    nombre: str


class CuentaOut(CuentaBase):
    id: int

    class Config:
        from_attributes = True
