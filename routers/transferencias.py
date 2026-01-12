from fastapi import APIRouter, Depends, Security, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date

from models.transferencia import Transferencia
from models.flujo import Flujo
from models.categoria import Categoria

from schemas.transferencia import (
    TransferenciaCreate,
    TransferenciaUpdate,
    TransferenciaOut
)

from dependencies import get_current_user, CurrentUser, get_db
from services.saldos_service import obtener_saldo_cuenta

from core.cache import cache_get, cache_set, cache_delete_pattern


router = APIRouter(
    prefix="/transferencias",
    tags=["Transferencias"]
)

# =========================================================
# CREAR TRANSFERENCIA
# =========================================================
@router.post("/", response_model=TransferenciaOut)
async def crear_transferencia(
    data: TransferenciaCreate,
    user: CurrentUser = Security(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crea una transferencia entre dos cuentas del usuario.

    Genera automáticamente:
    - Un Flujo Egreso
    - Un Flujo Ingreso
    Ambos vinculados a la transferencia.
    """

    if data.cuenta_origen_id == data.cuenta_destino_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta origen y destino no pueden ser la misma"
        )

    # 🔎 Categorías
    categoria_egreso = (
        db.query(Categoria)
        .filter(
            Categoria.usuario_id == user.id,
            Categoria.nombre == "Transferencias entre cuentas",
            Categoria.tipo_movimiento == "Egreso"
        )
        .first()
    )

    categoria_ingreso = (
        db.query(Categoria)
        .filter(
            Categoria.usuario_id == user.id,
            Categoria.nombre == "Transferencias entre cuentas",
            Categoria.tipo_movimiento == "Ingreso"
        )
        .first()
    )

    if not categoria_egreso or not categoria_ingreso:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Categorías de transferencia no configuradas"
        )

    # 🔒 Validación de saldo
    saldo_origen = obtener_saldo_cuenta(
        db,
        user.id,
        data.cuenta_origen_id
    )

    if saldo_origen < data.monto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Saldo insuficiente en la cuenta origen"
        )

    fecha_movimiento = date.today()

    transferencia = Transferencia(
        usuario_id=user.id,
        cuenta_origen_id=data.cuenta_origen_id,
        cuenta_destino_id=data.cuenta_destino_id,
        monto=data.monto,
        descripcion=data.descripcion,
        estado="confirmada"
    )

    try:
        db.add(transferencia)
        db.flush()

        flujo_egreso = Flujo(
            usuario_id=user.id,
            fecha=fecha_movimiento,
            descripcion=data.descripcion,
            categoria_id=categoria_egreso.id,
            cuenta_id=data.cuenta_origen_id,
            tipo_movimiento="Egreso",
            tipo_egreso="Variable",
            estado="confirmado",
            monto=data.monto,
            transferencia_id=transferencia.id
        )

        flujo_ingreso = Flujo(
            usuario_id=user.id,
            fecha=fecha_movimiento,
            descripcion=data.descripcion,
            categoria_id=categoria_ingreso.id,
            cuenta_id=data.cuenta_destino_id,
            tipo_movimiento="Ingreso",
            estado="confirmado",
            monto=data.monto,
            transferencia_id=transferencia.id
        )

        db.add_all([flujo_egreso, flujo_ingreso])
        db.commit()
        db.refresh(transferencia)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear la transferencia"
        )

    # 🧨 INVALIDACIÓN GLOBAL
    await cache_delete_pattern(f"transferencias:*:{user.id}*")
    await cache_delete_pattern(f"flujo:list:{user.id}")
    await cache_delete_pattern(f"saldos:*:{user.id}*")

    return transferencia


# =========================================================
# LISTAR TRANSFERENCIAS (CACHE)
# =========================================================
@router.get("/", response_model=list[TransferenciaOut])
async def listar_transferencias(
    user: CurrentUser = Security(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todas las transferencias del usuario autenticado.
    Resultado cacheado en Redis.
    """

    cache_key = f"transferencias:list:{user.id}"

    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    transferencias = (
        db.query(Transferencia)
        .filter(Transferencia.usuario_id == user.id)
        .order_by(Transferencia.created_at.desc(), Transferencia.id.desc())
        .all()
    )

    await cache_set(cache_key, transferencias)
    return transferencias


# =========================================================
# OBTENER TRANSFERENCIA (CACHE)
# =========================================================
@router.get("/{transferencia_id}", response_model=TransferenciaOut)
async def obtener_transferencia(
    transferencia_id: int,
    user: CurrentUser = Security(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene una transferencia específica del usuario.
    """

    cache_key = f"transferencias:detail:{user.id}:{transferencia_id}"

    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    transferencia = (
        db.query(Transferencia)
        .filter(
            Transferencia.id == transferencia_id,
            Transferencia.usuario_id == user.id
        )
        .first()
    )

    if not transferencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transferencia no encontrada"
        )

    await cache_set(cache_key, transferencia)
    return transferencia


# =========================================================
# ACTUALIZAR TRANSFERENCIA + FLUJOS
# =========================================================
@router.put("/{transferencia_id}", response_model=TransferenciaOut)
async def actualizar_transferencia(
    transferencia_id: int,
    data: TransferenciaUpdate,
    user: CurrentUser = Security(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza una transferencia y sincroniza sus flujos.
    """

    transferencia = (
        db.query(Transferencia)
        .filter(
            Transferencia.id == transferencia_id,
            Transferencia.usuario_id == user.id
        )
        .first()
    )

    if not transferencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transferencia no encontrada"
        )

    cuenta_origen = data.cuenta_origen_id or transferencia.cuenta_origen_id
    cuenta_destino = data.cuenta_destino_id or transferencia.cuenta_destino_id

    if cuenta_origen == cuenta_destino:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La cuenta origen y destino no pueden ser la misma"
        )

    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(transferencia, campo, valor)

    flujos = (
        db.query(Flujo)
        .filter(
            Flujo.transferencia_id == transferencia.id,
            Flujo.usuario_id == user.id
        )
        .all()
    )

    for flujo in flujos:
        flujo.cuenta_id = (
            cuenta_origen
            if flujo.tipo_movimiento == "Egreso"
            else cuenta_destino
        )
        flujo.monto = transferencia.monto
        flujo.descripcion = transferencia.descripcion

    db.commit()
    db.refresh(transferencia)

    # 🧨 INVALIDAR CACHE
    await cache_delete_pattern(f"transferencias:*:{user.id}*")
    await cache_delete_pattern(f"flujo:list:{user.id}")
    await cache_delete_pattern(f"saldos:*:{user.id}*")

    return transferencia


# =========================================================
# ELIMINAR TRANSFERENCIA + FLUJOS
# =========================================================
@router.delete("/{transferencia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_transferencia(
    transferencia_id: int,
    user: CurrentUser = Security(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Elimina una transferencia y sus flujos asociados.
    """

    transferencia = (
        db.query(Transferencia)
        .filter(
            Transferencia.id == transferencia_id,
            Transferencia.usuario_id == user.id
        )
        .first()
    )

    if not transferencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transferencia no encontrada"
        )

    db.query(Flujo).filter(
        Flujo.transferencia_id == transferencia.id
    ).delete()

    db.delete(transferencia)
    db.commit()

    # 🧨 INVALIDAR CACHE
    await cache_delete_pattern(f"transferencias:*:{user.id}*")
    await cache_delete_pattern(f"flujo:list:{user.id}")
    await cache_delete_pattern(f"saldos:*:{user.id}*")