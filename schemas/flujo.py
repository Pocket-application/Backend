from pydantic import BaseModel, field_validator
from datetime import date
from typing import Literal


class FlujoBase(BaseModel):
    fecha: date
    descripcion: str | None = None
    categoria_id: int
    cuenta_id: int
    tipo_movimiento: Literal["Ingreso", "Egreso"]
    tipo_egreso: Literal["Fijo", "Variable"] | None = None
    estado: Literal["pendiente", "confirmado"]
    monto: float

    @field_validator("tipo_egreso")
    @classmethod
    def validar_tipo_egreso(cls, v, info):
        tipo_mov = info.data.get("tipo_movimiento")
        if tipo_mov == "Egreso" and v is None:
            raise ValueError("tipo_egreso es obligatorio cuando tipo_movimiento es Egreso")
        if tipo_mov == "Ingreso" and v is not None:
            raise ValueError("tipo_egreso debe ser null cuando tipo_movimiento es Ingreso")
        return v
    
    @field_validator("tipo_egreso", mode="before")
    @classmethod
    def normalizar_vacio(cls, v):
        if v == "":
            return None
        return v


class FlujoCreate(FlujoBase):
    pass


class FlujoUpdate(BaseModel):
    fecha: date | None = None
    descripcion: str | None = None
    categoria_id: int | None = None
    cuenta_id: int | None = None
    estado: Literal["pendiente", "confirmado"] | None = None
    monto: float | None = None
    tipo_egreso: Literal["Fijo", "Variable"] | None = None
    
    @field_validator("tipo_egreso")
    @classmethod
    def validar_tipo_egreso(cls, v, info):
        tipo_mov = info.data.get("tipo_movimiento")
        if tipo_mov == "Egreso" and v is None:
            raise ValueError("tipo_egreso es obligatorio cuando tipo_movimiento es Egreso")
        if tipo_mov == "Ingreso" and v is not None:
            raise ValueError("tipo_egreso debe ser null cuando tipo_movimiento es Ingreso")
        return v
    
    @field_validator("tipo_egreso", mode="before")
    @classmethod
    def normalizar_vacio(cls, v):
        if v == "":
            return None
        return v


class FlujoOut(FlujoBase):
    id: int

    class Config:
        from_attributes = True
