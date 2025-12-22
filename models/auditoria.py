from sqlalchemy import Column, Integer, String, Text, JSON, TIMESTAMP
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.sql import func
from database import Base


class Auditoria(Base):
    """
    Registro de auditoría inmutable de todas las acciones relevantes del sistema.

    Este modelo:
    - Registra cada request procesado por el backend
    - Permite trazabilidad completa por usuario, IP y endpoint
    - Implementa firma criptográfica encadenada (anti-borrado / anti-manipulación)
    - Sirve como base para cumplimiento, forense y monitoreo de seguridad
    """

    __tablename__ = "auditoria"

    id = Column(Integer, primary_key=True)

    usuario_id = Column(
        String(9),
        nullable=True,
        doc="Identificador del usuario autenticado. Puede ser NULL para accesos anónimos."
    )

    metodo = Column(
        String(10),
        nullable=False,
        doc="Método HTTP utilizado en la solicitud (GET, POST, PUT, DELETE, etc)."
    )

    ruta = Column(
        Text,
        nullable=False,
        doc="Ruta del endpoint accedido."
    )

    status_code = Column(
        Integer,
        nullable=False,
        doc="Código de estado HTTP retornado por el servidor."
    )

    ip = Column(
        INET,
        nullable=True,
        doc="Dirección IP de origen del cliente."
    )

    body = Column(
        JSON,
        nullable=True,
        doc="Cuerpo de la solicitud (solo para operaciones que modifican estado)."
    )

    error = Column(
        Text,
        nullable=True,
        doc="Mensaje de error en caso de excepción durante el procesamiento."
    )

    duracion_ms = Column(
        Integer,
        nullable=False,
        doc="Tiempo total de procesamiento de la solicitud en milisegundos."
    )

    firma = Column(
        Text,
        nullable=False,
        doc="Firma criptográfica del registro actual."
    )

    firma_anterior = Column(
        Text,
        nullable=True,
        doc="Firma del registro anterior para encadenamiento criptográfico."
    )

    fecha = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Fecha y hora exacta en la que se registró el evento."
    )
