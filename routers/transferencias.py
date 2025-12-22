from fastapi import APIRouter, Depends, Security, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4

from models.transferencia import Transferencia
from models.flujo import Flujo
from schemas.transferencia import (
    TransferenciaCreate,
    TransferenciaUpdate,
    TransferenciaOut
)
from dependencies import get_current_user, CurrentUser, get_db

router = APIRouter(
    prefix="/transferencias",
    tags=["Transferencias"]
)

# =========================================================
# CREAR TRANSFERENCIA
# =========================================================
@router.post("/", response_model=TransferenciaOut)
def crear_transferencia(
        data: TransferenciaCreate,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Crea una transferencia entre dos cuentas del usuario.

    Automáticamente genera:
    - Un Egreso en la cuenta origen
    - Un Ingreso en la cuenta destino

    Ambos movimientos quedan vinculados a la transferencia.
    """
    if data.cuenta_origen_id == data.cuenta_destino_id:
        raise HTTPException(
            status_code=400,
            detail="La cuenta origen y destino no pueden ser la misma"
        )

    transferencia = Transferencia(
        id=uuid4(),
        usuario_id=user.id,
        cuenta_origen_id=data.cuenta_origen_id,
        cuenta_destino_id=data.cuenta_destino_id,
        monto=data.monto,
        descripcion=data.descripcion,
        estado="confirmada"
    )

    try:
        db.add(transferencia)

        # 🔴 Egreso
        flujo_egreso = Flujo(
            usuario_id=user.id,
            cuenta_id=data.cuenta_origen_id,
            tipo_movimiento="Egreso",
            tipo_egreso="Variable",
            estado="confirmado",
            monto=data.monto,
            descripcion=data.descripcion,
            transferencia_id=transferencia.id
        )

        # 🟢 Ingreso
        flujo_ingreso = Flujo(
            usuario_id=user.id,
            cuenta_id=data.cuenta_destino_id,
            tipo_movimiento="Ingreso",
            estado="confirmado",
            monto=data.monto,
            descripcion=data.descripcion,
            transferencia_id=transferencia.id
        )

        db.add_all([flujo_egreso, flujo_ingreso])
        db.commit()
        db.refresh(transferencia)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al crear la transferencia"
        )

    return transferencia


# =========================================================
# LISTAR TRANSFERENCIAS
# =========================================================
@router.get("/", response_model=list[TransferenciaOut])
def listar_transferencias(
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Lista todas las transferencias del usuario autenticado.
    """
    return (
        db.query(Transferencia)
        .filter(Transferencia.usuario_id == user.id)
        .order_by(Transferencia.id.desc())
        .all()
    )


# =========================================================
# OBTENER UNA TRANSFERENCIA
# =========================================================
@router.get("/{transferencia_id}", response_model=TransferenciaOut)
def obtener_transferencia(
        transferencia_id: str,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Obtiene una transferencia específica del usuario.

    Errores:
    -------
    404 Not Found
        Si la transferencia no existe.
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
        raise HTTPException(status_code=404, detail="Transferencia no encontrada")

    return transferencia


# =========================================================
# ACTUALIZAR TRANSFERENCIA + FLUJOS ASOCIADOS
# =========================================================
@router.put("/{transferencia_id}", response_model=TransferenciaOut)
def actualizar_transferencia(
        transferencia_id: str,
        data: TransferenciaUpdate,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Actualiza una transferencia y sincroniza sus flujos asociados.

    Si se modifican:
    - cuentas → se actualizan los flujos
    - monto → se ajustan ambos movimientos
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
        raise HTTPException(status_code=404, detail="Transferencia no encontrada")

    # 🔹 Validar cuentas si se modifican
    cuenta_origen = data.cuenta_origen_id or transferencia.cuenta_origen_id
    cuenta_destino = data.cuenta_destino_id or transferencia.cuenta_destino_id

    if cuenta_origen == cuenta_destino:
        raise HTTPException(
            status_code=400,
            detail="La cuenta origen y destino no pueden ser la misma"
        )

    # 🔹 Actualizar transferencia
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(transferencia, campo, valor)

    # 🔹 Actualizar flujos asociados
    flujos = (
        db.query(Flujo)
        .filter(
            Flujo.transferencia_id == transferencia.id,
            Flujo.usuario_id == user.id
        )
        .all()
    )

    for flujo in flujos:
        if flujo.tipo_movimiento == "Egreso":
            flujo.cuenta_id = cuenta_origen
            flujo.monto = transferencia.monto
            flujo.descripcion = transferencia.descripcion
        else:
            flujo.cuenta_id = cuenta_destino
            flujo.monto = transferencia.monto
            flujo.descripcion = transferencia.descripcion

    db.commit()
    db.refresh(transferencia)
    return transferencia


# =========================================================
# ELIMINAR TRANSFERENCIA (Y SUS FLUJOS)
# =========================================================
@router.delete("/{transferencia_id}")
def eliminar_transferencia(
        transferencia_id: str,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Elimina una transferencia y todos los movimientos asociados.
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
        raise HTTPException(status_code=404, detail="Transferencia no encontrada")

    db.query(Flujo).filter(
        Flujo.transferencia_id == transferencia.id
    ).delete()

    db.delete(transferencia)
    db.commit()

    return {"detail": "Transferencia eliminada correctamente"}
