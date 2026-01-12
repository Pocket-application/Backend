from datetime import date
from sqlalchemy.orm import Session
from decimal import Decimal

from repositories.saldos import (
    saldo_por_cuenta,
    saldo_rango,
    reajustar_saldo_cuenta
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


def reajustar_saldo(
    db: Session,
    usuario_id: str,
    cuenta_id: int,
    saldo_real: Decimal,
    descripcion: str | None = None
):
    """
    Reajusta el saldo real de una cuenta.

    Se registra automáticamente como:
    - Ingreso o Egreso
    - Categoría: Reajuste de saldo
    """

    if saldo_real < 0:
        raise ValueError("El saldo real no puede ser negativo")

    saldo_real_decimal = Decimal(str(saldo_real))
    
    return reajustar_saldo_cuenta(
        db,
        usuario_id,
        cuenta_id,
        saldo_real_decimal,
        descripcion
    )