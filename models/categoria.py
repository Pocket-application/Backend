from sqlalchemy import Column, Integer, String, ForeignKey, CheckConstraint, UniqueConstraint
from database import Base

class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(String(7), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String, nullable=False)
    tipo_movimiento = Column(String, nullable=False)

    __table_args__ = (
        CheckConstraint("tipo_movimiento IN ('Ingreso','Egreso','Ambos')"),
        UniqueConstraint("usuario_id", "nombre", name="uq_usuario_categoria"),
    )
