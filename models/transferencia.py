from sqlalchemy import Column, String, Numeric, DateTime, Enum, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid

EstadoTransferenciaEnum = Enum(
    "Pendiente",
    "Confirmado",
    name="estado_transferencia_enum",
    create_type=False
)

from database import Base


class Transferencia(Base):
    """
    Operación financiera que mueve fondos entre cuentas.

    Una transferencia:
    - Genera automáticamente dos flujos (ingreso y egreso)
    - Es atómica y transaccional
    - No modifica saldos directamente
    """

    __tablename__ = "transferencias"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
        doc="Identificador único de la transferencia."
    )

    usuario_id = Column(
        String(9),
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Usuario que ejecuta la transferencia."
    )

    cuenta_origen_id = Column(
        Integer,
        nullable=False,
        index=True,
        doc="Cuenta desde la cual se egresan los fondos."
    )

    cuenta_destino_id = Column(
        Integer,
        nullable=False,
        index=True,
        doc="Cuenta que recibe los fondos."
    )

    monto = Column(
        Numeric(14, 2),
        nullable=False,
        doc="Monto transferido."
    )

    descripcion = Column(
        String,
        nullable=True,
        doc="Descripción opcional de la transferencia."
    )

    estado = Column(
        EstadoTransferenciaEnum,
        nullable=False,
        doc="Estado actual de la transferencia."
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        doc="Fecha y hora de creación."
    )

