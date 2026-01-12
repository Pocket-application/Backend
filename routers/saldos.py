from fastapi import APIRouter, Depends, Security, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from dependencies import get_db, get_current_user, CurrentUser
from services.saldos_service import (
    obtener_saldos_usuario,
    obtener_saldos_rango,
    reajustar_saldo
)
from schemas.saldos import SaldoCuentaOut, ReajusteSaldoIn
from core.cache import cache_get, cache_set, cache_delete_pattern

router = APIRouter(
    prefix="/saldos",
    tags=["Saldos"]
)

@router.get("/cuentas", response_model=List[SaldoCuentaOut])
async def saldos_por_cuenta(
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Obtiene el saldo actual de todas las cuentas del usuario.

    El cálculo se realiza mediante funciones SQL optimizadas
    en la base de datos.
    """
    cache_key = f"saldos:cuentas:{user.id}"

    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    data = obtener_saldos_usuario(db, user.id)

    await cache_set(cache_key, data)

    return data


@router.get("/rango", response_model=List[SaldoCuentaOut])
async def saldos_por_rango(
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
    if fecha_inicio > fecha_fin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha inicial no puede ser mayor a la final"
        )

    cache_key = (
        f"saldos:rango:{user.id}:"
        f"{fecha_inicio.isoformat()}:{fecha_fin.isoformat()}"
    )

    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        data = obtener_saldos_rango(
            db,
            user.id,
            fecha_inicio,
            fecha_fin
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    await cache_set(cache_key, data)

    return data

@router.post("/reajuste", status_code=status.HTTP_204_NO_CONTENT)
async def reajustar_saldo_cuenta(
    payload: ReajusteSaldoIn,
    user: CurrentUser = Security(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reajusta el saldo real de una cuenta.

    Se genera automáticamente un movimiento contable
    (Ingreso o Egreso) con la categoría:
        'Reajuste de saldo'
    """
    try:
        reajustar_saldo(
            db=db,
            usuario_id=user.id,
            cuenta_id=payload.cuenta_id,
            saldo_real=payload.saldo_real,
            descripcion=payload.descripcion
        )
        # 🧨 INVALIDACIÓN DE CACHE
        await cache_delete_pattern(f"saldos:cuentas:{user.id}")
        await cache_delete_pattern(f"saldos:rango:{user.id}:*")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))