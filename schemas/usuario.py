from pydantic import BaseModel, EmailStr, Field


class UsuarioCreate(BaseModel):
    nombre: str
    apellido: str
    correo: EmailStr
    password: str = Field(min_length=8)


class UsuarioOut(BaseModel):
    id: str
    nombre: str
    apellido: str
    correo: EmailStr
    telefono: str | None = None
    rol: str
    verificado: bool

    class Config:
        from_attributes = True


class UsuarioUpdateNombre(BaseModel):
    nombre: str
    apellido: str


class UsuarioUpdateCorreo(BaseModel):
    correo: EmailStr


class UsuarioUpdateTelefono(BaseModel):
    telefono: str


class UsuarioUpdatePassword(BaseModel):
    password_actual: str
    password_nueva: str = Field(min_length=8)
