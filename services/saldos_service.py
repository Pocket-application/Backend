from datetime import date
from sqlalchemy.orm import Session

from repositories.saldos import (
    saldo_por_cuenta,
    saldo_rango
)


def obtener_saldos_usuario(
    db: Session,
    usuario_id: str
):
    """
    Obtiene el saldo actual de todas las cuentas del usuario.

    La información proviene de la función SQL:
        fn_saldo_por_cuenta(uid)

    Retorna una lista de filas con:
    - cuenta_id
    - cuenta
    - saldo
    """
    return saldo_por_cuenta(db, usuario_id)


def obtener_saldos_rango(
    db: Session,
    usuario_id: str,
    inicio: date,
    fin: date
):
    """
    Obtiene los saldos del usuario dentro de un rango de fechas.
    """
    if inicio > fin:
        raise ValueError(
            "La fecha inicial no puede ser mayor a la final"
        )

    return saldo_rango(db, usuario_id, inicio, fin)


def obtener_saldo_cuenta(
    db: Session,
    usuario_id: str,
    cuenta_id: int
) -> float:
    """
    Obtiene el saldo actual de una cuenta específica del usuario.
    """

    resultados = saldo_por_cuenta(db, usuario_id)

    for row in resultados:
        if row["cuenta_id"] == cuenta_id:
            return float(row["saldo"])

    raise ValueError(
        "La cuenta no existe o no pertenece al usuario"
    )
