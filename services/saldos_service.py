from datetime import date
from sqlalchemy.orm import Session
from repositories.saldos import saldo_por_cuenta, saldo_rango

def obtener_saldos_usuario(db: Session, usuario_id: str):
    return saldo_por_cuenta(db, usuario_id)


def obtener_saldos_rango(
    db: Session,
    usuario_id: str,
    inicio: date,
    fin: date
):
    if inicio > fin:
        raise ValueError("La fecha inicial no puede ser mayor a la final")

    return saldo_rango(db, usuario_id, inicio, fin)
