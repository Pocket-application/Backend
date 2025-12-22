from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey
from database import Base

class RefreshToken(Base):
    """
    Token de renovación de autenticación (JWT).

    Permite:
    - Mantener sesiones activas sin re-login
    - Revocar accesos de forma controlada
    """

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)

    usuario_id = Column(
        String(7),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        doc="Usuario propietario del refresh token."
    )

    token = Column(
        String,
        nullable=False,
        doc="Token de refresco único y seguro."
    )

    expira = Column(
        TIMESTAMP,
        nullable=False,
        doc="Fecha y hora de expiración del token."
    )
