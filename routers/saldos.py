from fastapi import APIRouter, Depends, Security, HTTPException
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from dependencies import get_db, get_current_user, CurrentUser
from services.saldos_service import (
    obtener_saldos_usuario,
    obtener_saldos_rango
)
from schemas.saldos import SaldoCuentaOut

router = APIRouter(
    prefix="/saldos",
    tags=["Saldos"]
)

@router.get("/cuentas", response_model=List[SaldoCuentaOut])
def saldos_por_cuenta(
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Obtiene el saldo actual de todas las cuentas del usuario.

    El cálculo se realiza mediante funciones SQL optimizadas
    en la base de datos.
    """
    return obtener_saldos_usuario(db, user.id)


@router.get("/rango", response_model=List[SaldoCuentaOut])
def saldos_por_rango(
        fecha_inicio: date,
        fecha_fin: date,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Obtiene los saldos del usuario dentro de un rango de fechas.

    Parámetros:
    ----------
    fecha_inicio : date
    fecha_fin : date

    Errores:
    -------
    400 Bad Request
        Si el rango de fechas es inválido.
    """
    try:
        return obtener_saldos_rango(
            db,
            user.id,
            fecha_inicio,
            fecha_fin
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
