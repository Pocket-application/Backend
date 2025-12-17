from pydantic import BaseModel

class CategoriaCreate(BaseModel):
    nombre: str
    tipo_movimiento: str

class CategoriaOut(BaseModel):
    id: int
    nombre: str
    tipo_movimiento: str

    class Config:
        from_attributes = True
