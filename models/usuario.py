from sqlalchemy import Column, String, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.sql import func
from database import Base


# =========================================================
# ENUM PostgreSQL: rol_usuario_enum
# =========================================================
rol_usuario_enum = ENUM(
    "user",
    "admin",
    name="rol_usuario_enum",
    create_type=False
)


class Usuario(Base):
    """
    Representa un usuario del sistema.

    El usuario:
    - Puede tener múltiples cuentas, categorías y movimientos
    - Está sujeto a control de roles mediante ENUM PostgreSQL
    - Puede tener teléfono validado a 10 dígitos
    - Es completamente auditable
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
        index=True,
        doc="Correo electrónico del usuario."
    )

    telefono = Column(
        String(10),
        nullable=True,
        index=True,
        doc="Número de teléfono del usuario (exactamente 10 dígitos)."
    )

    password = Column(
        String,
        nullable=False,
        doc="Hash de la contraseña del usuario."
    )

    verificado = Column(
        Boolean,
        default=False,
        doc="Indica si el usuario ha sido verificado."
    )

    rol = Column(
        rol_usuario_enum,
        nullable=False,
        default="user",
        doc="Rol del usuario dentro del sistema."
    )

    fecha_registro = Column(
        TIMESTAMP,
        server_default=func.now(),
        doc="Fecha de registro del usuario."
    )
