from pydantic import BaseModel, EmailStr, Field


class UsuarioCreate(BaseModel):
    nombre: str
    apellido: str
    correo: EmailStr
    password: str = Field(min_length=8)
    telefono: str | None = Field(
        default=None,
        pattern=r"^\d{10}$",
        description="Número de teléfono de 10 dígitos"
    )


class UsuarioOut(BaseModel):
    nombre: str
    apellido: str
    correo: EmailStr
    telefono: str | None = None

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
