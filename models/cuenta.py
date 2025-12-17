from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from database import Base

class Cuenta(Base):
    __tablename__ = "cuentas"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(String(7), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("usuario_id", "nombre", name="uq_usuario_cuenta"),
    )
