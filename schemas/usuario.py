from pydantic import BaseModel, EmailStr

class UsuarioCreate(BaseModel):
    nombre: str
    apellido: str
    correo: EmailStr
    password: str

class UsuarioOut(BaseModel):
    id: str
    nombre: str
    apellido: str
    correo: EmailStr
    verificado: bool

    class Config:
        from_attributes = True
