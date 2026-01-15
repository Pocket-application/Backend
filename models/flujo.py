from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    Numeric,
    ForeignKey,
    CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
from sqlalchemy import Enum
from datetime import date

TipoMovimientoEnum = Enum(
    "Ingreso",
    "Egreso",
    name="tipo_movimiento_enum",
    create_type=False
)

EstadoEnum = Enum(
    "Pendiente",
    "Confirmado",
    name="estado_movimiento_enum",
    create_type=False
)

TipoEgresoEnum = Enum(
    "Fijo",
    "Variable",
    name="tipo_egreso_enum",
    create_type=False
)

class Flujo(Base):
    """
    Registro individual de un movimiento financiero.

    Un flujo:
    - Representa un ingreso o egreso
    - Puede estar asociado a una transferencia
    - Es la unidad base para cálculos financieros
    - Mantiene consistencia fuerte mediante constraints
    """

    __tablename__ = "flujo"

    id = Column(Integer, primary_key=True)

    usuario_id = Column(
        String(7),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Usuario propietario del movimiento."
    )

    fecha = Column(
        Date,
        nullable=False,
        default= date.today,
        doc="Fecha efectiva del movimiento."
    )

    descripcion = Column(
        String,
        doc="Descripción opcional del movimiento."
    )

    categoria_id = Column(
        Integer,
        ForeignKey("categorias.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Categoría asociada al movimiento."
    )

    cuenta_id = Column(
        Integer,
        ForeignKey("cuentas.id", ondelete="RESTRICT"),
        nullable=False,
        doc="Cuenta afectada por el movimiento."
    )

    transferencia_id = Column(
        Integer,
        ForeignKey("transferencias.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        doc="Transferencia asociada, si aplica."
    )

    tipo_movimiento = Column(
        TipoMovimientoEnum,
        nullable=False,
        doc="Tipo de movimiento: Ingreso o Egreso."
    )

    tipo_egreso = Column(
        TipoEgresoEnum,
        nullable=True,
        doc="Clasificación del egreso: Fijo o Variable. Obligatorio si es egreso."
    )

    estado = Column(
        EstadoEnum,
        nullable=False,
        doc="Estado del movimiento: pendiente o confirmado."
    )

    monto = Column(
        Numeric(14, 2),
        nullable=False,
        doc="Valor monetario del movimiento."
    )

    __table_args__ = (
        # Tipo de movimiento permitido
        CheckConstraint(
            "tipo_movimiento IN ('Ingreso', 'Egreso')",
            name="ck_flujo_tipo_movimiento"
        ),

        # Estado permitido
        CheckConstraint(
            "estado IN ('Pendiente', 'Confirmado')",
            name="ck_flujo_estado"
        ),

        # Tipo de egreso permitido
        CheckConstraint(
            "tipo_egreso IS NULL OR tipo_egreso IN ('Fijo', 'Variable')",
            name="ck_flujo_tipo_egreso"
        ),

        # Regla fuerte: si es Egreso → tipo_egreso obligatorio
        CheckConstraint(
            """
            (tipo_movimiento = 'Ingreso' AND tipo_egreso IS NULL)
            OR
            (tipo_movimiento = 'Egreso' AND tipo_egreso IS NOT NULL)
            """,
            name="ck_flujo_egreso_consistencia"
        ),
    )
