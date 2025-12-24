from sqlalchemy import Column, Integer, String, ForeignKey, CheckConstraint, UniqueConstraint, Enum
from database import Base
import enum


class TipoMovimientoEnum(str, enum.Enum):
    Ingreso = "Ingreso"
    Egreso = "Egreso"


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
        String(9),
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
        Enum(TipoMovimientoEnum, name="tipo_movimiento_enum", create_type=False),
        nullable=False,
        doc="Tipo de movimiento permitido: Ingreso o Egreso"
    )


    __table_args__ = (
        CheckConstraint(
            "tipo_movimiento IN ('Ingreso','Egreso')",
            name="ck_categoria_tipo_movimiento"
        ),
        UniqueConstraint(
            "usuario_id",
            "nombre",
            "tipo_movimiento",
            name="uq_usuario_categoria"
        ),
    )
