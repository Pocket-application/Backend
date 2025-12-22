from sqlalchemy import Column, String, Boolean, TIMESTAMP, CheckConstraint
from sqlalchemy.sql import func
from database import Base

class Usuario(Base):
    """
    Representa un usuario del sistema.

    El usuario:
    - Puede tener múltiples cuentas, categorías y movimientos
    - Está sujeto a control de roles
    - Puede ser auditado en todas sus acciones
    """

    __tablename__ = "usuarios"

    id = Column(
        String(9),
        primary_key=True,
        index=True,
        doc="Identificador único del usuario."
    )

    nombre = Column(
        String,
        nullable=False,
        doc="Nombre del usuario."
    )

    apellido = Column(
        String,
        nullable=False,
        doc="Apellido del usuario."
    )

    correo = Column(
        String,
        unique=True,
        nullable=False,
        doc="Correo electrónico del usuario."
    )

    password = Column(
        String,
        nullable=False,
        doc="Hash de la contraseña del usuario."
    )

    verificado = Column(
        Boolean,
        default=True,
        doc="Indica si el usuario ha sido verificado."
    )

    rol = Column(
        String,
        default="user",
        nullable=False,
        doc="Rol del usuario dentro del sistema."
    )

    fecha_registro = Column(
        TIMESTAMP,
        server_default=func.now(),
        doc="Fecha de registro del usuario."
    )


    __table_args__ = (
        CheckConstraint("rol IN ('user','admin')"),
    )
