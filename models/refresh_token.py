from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base

class RefreshToken(Base):
    """
    Token de renovación de autenticación (JWT).

    Permite:
    - Mantener sesiones activas sin re-login
    - Revocar accesos de forma controlada
    """

    __tablename__ = "refresh_tokens"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    usuario_id = Column(
        String(9),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Usuario propietario del refresh token."
    )

    token = Column(
        String,
        nullable=False,
        unique=True,
        index=True,
        doc="Token de refresco único y seguro."
    )

    expira = Column(
        DateTime(timezone=True),
        nullable=False,
        doc="Fecha y hora de expiración del token (UTC)."
    )

    fecha_creacion = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        doc="Fecha de creación del refresh token."
    )
