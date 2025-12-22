from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from database import Base


class Cuenta(Base):
    """
    Representa una cuenta financiera del usuario.

    Una cuenta:
    - Almacena saldo implícito a través de flujos
    - Puede participar en transferencias
    - Es única por usuario
    """

    __tablename__ = "cuentas"

    id = Column(Integer, primary_key=True)

    usuario_id = Column(
        String(7),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        doc="Usuario propietario de la cuenta."
    )

    nombre = Column(
        String,
        nullable=False,
        doc="Nombre identificador de la cuenta (ej. Ahorros, Efectivo, Banco)."
    )

    __table_args__ = (
        UniqueConstraint(
            "usuario_id",
            "nombre",
            name="uq_usuario_cuenta"
        ),
    )
