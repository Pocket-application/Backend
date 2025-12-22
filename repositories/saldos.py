from sqlalchemy.orm import Session
from sqlalchemy import text


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
    """)

    result = db.execute(sql, {"uid": usuario_id})
    return result.fetchall()


def saldo_rango(
    db: Session,
    usuario_id: str,
    fecha_inicio,
    fecha_fin
):
    """
    Obtiene el saldo consolidado del usuario dentro de un rango de fechas.

    Esta función permite realizar análisis financiero histórico,
    como balances por período, reportes mensuales o comparaciones
    entre rangos de tiempo.

    El cálculo se delega a una función almacenada en PostgreSQL:
        finanzas.fn_saldo_rango(
            usuario_id,
            fecha_inicio,
            fecha_fin
        )

    Parámetros:
    ----------
    db : Session
        Sesión activa de SQLAlchemy.
    usuario_id : str
        Identificador del usuario propietario de los movimientos.
    fecha_inicio : date
        Fecha inicial del rango (inclusive).
    fecha_fin : date
        Fecha final del rango (inclusive).

    Retorna:
    -------
    list
        Lista de resultados calculados por la función SQL.
        Normalmente incluye información como:
        - saldo_inicial
        - total_ingresos
        - total_egresos
        - saldo_final
    """

    sql = text("""
        SELECT *
        FROM finanzas.fn_saldo_rango(
            :uid,
            :fecha_inicio,
            :fecha_fin
        )
    """)

    result = db.execute(
        sql,
        {
            "uid": usuario_id,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin
        }
    )

    return result.fetchall()
