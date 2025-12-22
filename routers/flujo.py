from fastapi import APIRouter, Depends, Security, HTTPException
from sqlalchemy.orm import Session

from models.flujo import Flujo
from schemas.flujo import FlujoCreate, FlujoUpdate, FlujoOut
from dependencies import get_current_user, CurrentUser, get_db

router = APIRouter(
    prefix="/flujo",
    tags=["Flujo"]
)

# =========================================================
# CREAR MOVIMIENTO
# =========================================================
@router.post("/", response_model=FlujoOut)
def crear_movimiento(
        data: FlujoCreate,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Registra un movimiento financiero (Ingreso o Egreso).

    Puede ser:
    - Un movimiento manual
    - Parte de una transferencia (vinculado por transferencia_id)

    Reglas:
    -------
    - Si es Egreso, tipo_egreso es obligatorio
    - Si es Ingreso, tipo_egreso debe ser NULL
    """
    movimiento = Flujo(
        usuario_id=user.id,
        fecha=data.fecha,
        descripcion=data.descripcion,
        categoria_id=data.categoria_id,
        cuenta_id=data.cuenta_id,
        tipo_movimiento=data.tipo_movimiento,
        tipo_egreso=data.tipo_egreso,
        estado=data.estado,
        monto=data.monto,
        transferencia_id=data.transferencia_id
    )

    db.add(movimiento)
    db.commit()
    db.refresh(movimiento)
    return movimiento


# =========================================================
# LISTAR MOVIMIENTOS DEL USUARIO
# =========================================================
@router.get("/", response_model=list[FlujoOut])
def listar_movimientos(
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Lista todos los movimientos financieros del usuario.

    Se ordenan por fecha descendente y luego por ID.
    """
    return (
        db.query(Flujo)
        .filter(Flujo.usuario_id == user.id)
        .order_by(Flujo.fecha.desc(), Flujo.id.desc())
        .all()
    )


# =========================================================
# ACTUALIZAR MOVIMIENTO (PATCH SEMÁNTICO)
# =========================================================
@router.put("/{movimiento_id}", response_model=FlujoOut)
def actualizar_movimiento(
        movimiento_id: int,
        data: FlujoUpdate,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Actualiza parcialmente un movimiento financiero existente.

    Solo se modifican los campos enviados en la petición.
    """
    movimiento = (
        db.query(Flujo)
        .filter(
            Flujo.id == movimiento_id,
            Flujo.usuario_id == user.id
        )
        .first()
    )

    if not movimiento:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")

    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(movimiento, campo, valor)

    db.commit()
    db.refresh(movimiento)
    return movimiento


# =========================================================
# ELIMINAR MOVIMIENTO
# =========================================================
@router.delete("/{movimiento_id}")
def eliminar_movimiento(
        movimiento_id: int,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Elimina un movimiento financiero del usuario.

    No permite eliminar movimientos que estén ligados
    a una transferencia.
    """
    movimiento = (
        db.query(Flujo)
        .filter(
            Flujo.id == movimiento_id,
            Flujo.usuario_id == user.id
        )
        .first()
    )

    if not movimiento:
        raise HTTPException(status_code=404, detail="Movimiento no encontrado")

    db.delete(movimiento)
    db.commit()

    return {"detail": "Movimiento eliminado correctamente"}
