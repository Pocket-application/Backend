from sqlalchemy import Column, Integer, String, ForeignKey, CheckConstraint, UniqueConstraint
from database import Base


class Categoria(Base):
    """
    Clasificación lógica de movimientos financieros del usuario.

    Las categorías:
    - Permiten agrupar ingresos y egresos
    - Son específicas por usuario
    - Definen qué tipo de movimiento pueden contener
    """

    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True)

    usuario_id = Column(
        String(7),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        doc="Usuario propietario de la categoría."
    )

    nombre = Column(
        String,
        nullable=False,
        doc="Nombre descriptivo de la categoría."
    )

    tipo_movimiento = Column(
        String,
        nullable=False,
        doc="Tipo de movimiento permitido: Ingreso, Egreso o Ambos."
    )

    __table_args__ = (
        CheckConstraint(
            "tipo_movimiento IN ('Ingreso','Egreso','Ambos')",
            name="ck_categoria_tipo_movimiento"
        ),
        UniqueConstraint(
            "usuario_id",
            "nombre",
            name="uq_usuario_categoria"
        ),
    )
