from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, CheckConstraint
from database import Base

class Flujo(Base):
    __tablename__ = "flujo"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(String(7), ForeignKey("usuarios.id", ondelete="CASCADE"))
    fecha = Column(Date, nullable=False)
    descripcion = Column(String)
    categoria_id = Column(Integer, ForeignKey("categorias.id", ondelete="RESTRICT"))
    cuenta_id = Column(Integer, ForeignKey("cuentas.id", ondelete="RESTRICT"))
    tipo_movimiento = Column(String, nullable=False)
    estado = Column(String, nullable=False)
    monto = Column(Numeric(14,2), nullable=False)

    __table_args__ = (
        CheckConstraint("tipo_movimiento IN ('Ingreso','Egreso')"),
        CheckConstraint("estado IN ('pendiente','confirmado')"),
    )
