from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey
from database import Base

class Transferencia(Base):
    __tablename__ = "transferencias"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(String(7), ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    fecha = Column(Date, nullable=False)
    cuenta_salida = Column(Integer, ForeignKey("cuentas.id", ondelete="RESTRICT"), nullable=False)
    cuenta_destino = Column(Integer, ForeignKey("cuentas.id", ondelete="RESTRICT"), nullable=False)
    monto = Column(Numeric(14,2), nullable=False)
