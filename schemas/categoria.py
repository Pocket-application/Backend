from pydantic import BaseModel
from typing import Literal


class CategoriaBase(BaseModel):
    nombre: str
    tipo_movimiento: Literal["Ingreso", "Egreso"]


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    nombre: str | None = None
    tipo_movimiento: Literal["Ingreso", "Egreso"] | None = None


class CategoriaOut(CategoriaBase):
    id: int

    class Config:
        from_attributes = True
