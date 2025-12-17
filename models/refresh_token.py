from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey
from database import Base

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(String(7), ForeignKey("usuarios.id", ondelete="CASCADE"))
    token = Column(String, nullable=False)
    expira = Column(TIMESTAMP, nullable=False)
