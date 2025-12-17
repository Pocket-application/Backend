from sqlalchemy import Column, String, Boolean, TIMESTAMP, CheckConstraint
from sqlalchemy.sql import func
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(String(7), primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    apellido = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False)
    contraseña = Column(String, nullable=False)
    verificado = Column(Boolean, default=True)
    rol = Column(String, default="user", nullable=False)
    fecha_registro = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = (
        CheckConstraint("rol IN ('user','admin')"),
    )
