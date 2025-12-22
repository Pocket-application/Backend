from fastapi import APIRouter, Depends, Security, HTTPException
from sqlalchemy.orm import Session

from schemas.cuenta import CuentaCreate, CuentaUpdate, CuentaOut
from models.cuenta import Cuenta
from dependencies import get_db, get_current_user, CurrentUser

router = APIRouter(
    prefix="/cuentas",
    tags=["Cuentas"]
)

# =========================================================
# CREAR CUENTA
# =========================================================
@router.post("/", response_model=CuentaOut)
def crear_cuenta(
        data: CuentaCreate,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Crea una nueva cuenta financiera para el usuario autenticado.

    El nombre de la cuenta debe ser único por usuario.

    Errores:
    -------
    400 Bad Request
        Si la cuenta ya existe.
    """
    # 🔹 Evitar duplicados por usuario
    if db.query(Cuenta).filter(
        Cuenta.usuario_id == user.id,
        Cuenta.nombre == data.nombre
    ).first():
        raise HTTPException(status_code=400, detail="La cuenta ya existe")

    cuenta = Cuenta(
        nombre=data.nombre,
        usuario_id=user.id
    )

    db.add(cuenta)
    db.commit()
    db.refresh(cuenta)
    return cuenta


# =========================================================
# LISTAR CUENTAS DEL USUARIO
# =========================================================
@router.get("/", response_model=list[CuentaOut])
def listar_cuentas(
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Lista todas las cuentas del usuario autenticado.

    Se ordenan alfabéticamente por nombre.
    """
    return (
        db.query(Cuenta)
        .filter(Cuenta.usuario_id == user.id)
        .order_by(Cuenta.nombre)
        .all()
    )


# =========================================================
# ACTUALIZAR CUENTA
# =========================================================
@router.put("/{cuenta_id}", response_model=CuentaOut)
def actualizar_cuenta(
        cuenta_id: int,
        data: CuentaUpdate,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Actualiza el nombre de una cuenta del usuario.

    Errores:
    -------
    404 Not Found
        Si la cuenta no existe o no pertenece al usuario.
    """
    cuenta = db.query(Cuenta).filter(
        Cuenta.id == cuenta_id,
        Cuenta.usuario_id == user.id
    ).first()

    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    cuenta.nombre = data.nombre

    db.commit()
    db.refresh(cuenta)
    return cuenta


# =========================================================
# ELIMINAR CUENTA
# =========================================================
@router.delete("/{cuenta_id}")
def eliminar_cuenta(
        cuenta_id: int,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Elimina una cuenta del usuario autenticado.

    No se puede eliminar una cuenta si tiene movimientos asociados.
    """
    cuenta = db.query(Cuenta).filter(
        Cuenta.id == cuenta_id,
        Cuenta.usuario_id == user.id
    ).first()

    if not cuenta:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    db.delete(cuenta)
    db.commit()

    return {"detail": "Cuenta eliminada correctamente"}
