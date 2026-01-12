from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import text, Integer, String, Numeric
from sqlalchemy.exc import SQLAlchemyError, DBAPIError
from decimal import Decimal


def saldo_por_cuenta(db: Session, usuario_id: str):
    """
    Obtiene el saldo actual de todas las cuentas de un usuario.

    Esta función actúa como un repositorio de lectura que delega
    el cálculo del saldo a una función almacenada en PostgreSQL,
    garantizando consistencia, performance y reutilización de lógica.

    Internamente ejecuta la función:
        finanzas.fn_saldo_por_cuenta(usuario_id)

    Parámetros:
    ----------
    db : Session
        Sesión activa de SQLAlchemy utilizada para ejecutar la consulta.
    usuario_id : str
        Identificador único del usuario del cual se desean obtener los saldos.

    Retorna:
    -------
    list
        Lista de registros con el saldo calculado por cuenta.
        El formato depende de la definición de la función SQL,
        típicamente incluyendo:
        - cuenta_id
        - nombre_cuenta
        - saldo
    """

    sql = text("""
        SELECT *
        FROM finanzas.fn_saldo_por_cuenta(:uid)
    """).columns(
        cuenta_id=Integer,
        cuenta=String,
        saldo=Numeric
    )

    result = db.execute(sql, {"uid": usuario_id})

    filas = result.mappings().all()

    return filas


def saldo_rango(
    db: Session,
    usuario_id: str,
    fecha_inicio: date,
    fecha_fin: date
):
    """
    Obtiene el saldo consolidado del usuario dentro de un rango de fechas.
    """

    # 🔒 Validaciones de entrada (fail fast)
    if not usuario_id or not usuario_id.strip():
        raise ValueError("El usuario_id es obligatorio")

    if fecha_inicio is None or fecha_fin is None:
        raise ValueError("Las fechas no pueden ser nulas")

    if not isinstance(fecha_inicio, date) or not isinstance(fecha_fin, date):
        raise TypeError("fecha_inicio y fecha_fin deben ser de tipo date")

    if fecha_inicio > fecha_fin:
        raise ValueError(
            "La fecha inicial no puede ser mayor que la fecha final"
        )

    sql = text("""
        SELECT
            cuenta_id,
            cuenta,
            saldo
        FROM finanzas.fn_saldo_rango(
            :uid,
            :fecha_inicio,
            :fecha_fin
        )
    """)

    try:
        result = db.execute(
            sql,
            {
                "uid": usuario_id,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin
            }
        )

        rows = result.fetchall()

    except DBAPIError as e:
        # 🔐 Errores provenientes de PostgreSQL (RAISE EXCEPTION)
        raise ValueError(
            "Error al calcular el saldo por rango. "
            "Verifique los parámetros enviados."
        ) from e

    except SQLAlchemyError as e:
        # 🔥 Error inesperado de infraestructura
        raise RuntimeError(
            "Error interno al consultar el saldo"
        ) from e

    # 🧠 Contrato de retorno claro
    return [
        {
            "cuenta_id": row.cuenta_id,
            "cuenta": row.cuenta,
            "saldo": float(row.saldo)
        }
        for row in rows
    ]
    
def reajustar_saldo_cuenta(
    db: Session,
    usuario_id: str,
    cuenta_id: int,
    saldo_real: Decimal,
    descripcion: str | None = None
) -> None:
    """
    Ejecuta la función SQL fn_reajustar_saldo_cuenta.

    La lógica de validación y cálculo vive en PostgreSQL.
    """
    if not usuario_id:
        raise ValueError("Usuario inválido")

    if cuenta_id <= 0:
        raise ValueError("Cuenta inválida")

    if saldo_real < 0:
        raise ValueError("El saldo real no puede ser negativo")

    sql = text("""
        SELECT finanzas.fn_reajustar_saldo_cuenta(
            :usuario_id,
            :cuenta_id,
            :saldo_real,
            :descripcion
        )
    """)

    try:
        db.execute(
            sql,
            {
                "usuario_id": usuario_id,
                "cuenta_id": cuenta_id,
                "saldo_real": saldo_real,
                "descripcion": descripcion
            }
        )
        db.commit()

    except DBAPIError as e:
        raise ValueError(
            "No fue posible reajustar el saldo de la cuenta"
        ) from e