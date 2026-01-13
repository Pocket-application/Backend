from fastapi import APIRouter, Depends, HTTPException, Security
from sqlalchemy.orm import Session

from schemas.usuario import (
    UsuarioCreate,
    UsuarioOut,
    UsuarioUpdateNombre,
    UsuarioUpdateCorreo,
    UsuarioUpdateTelefono,
    UsuarioUpdatePassword
)
from models.usuario import Usuario
from security_tokens import get_password_hash, verify_password
from dependencies import get_db, get_current_user, CurrentUser
from utils.id_generator import generate_unique_user_id
from services.categorias import crear_categorias_default

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)

# =========================================================
# REGISTRO DE USUARIO (PÚBLICO)
# =========================================================
@router.post("/", response_model=UsuarioOut)
def registrar_usuario(
        data: UsuarioCreate,
        db: Session = Depends(get_db)
    ):
    """
    Registra un nuevo usuario en el sistema.

    Endpoint público.
    Genera un ID único y almacena la contraseña hasheada.
    """
    # 🔹 Verificar correo único
    if db.query(Usuario).filter(Usuario.correo == data.correo).first():
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    user_id = generate_unique_user_id(db)

    user = Usuario(
        id=user_id,
        nombre=data.nombre,
        apellido=data.apellido,
        correo=data.correo,
        password=get_password_hash(data.password),
        telefono=data.telefono,
        rol="user"
    )

    try:
        db.add(user)
        db.flush()  # importante para tener el usuario antes del commit

        crear_categorias_default(user.id, db)

        db.commit()
        db.refresh(user)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error al registrar el usuario"
        )

    return user


# =========================================================
# CAMBIAR NOMBRE Y APELLIDO
# =========================================================
@router.put("/nombre", response_model=UsuarioOut)
def actualizar_nombre(
        data: UsuarioUpdateNombre,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Actualiza el nombre y apellido del usuario autenticado.
    """
    usuario = db.get(Usuario, user.id)
    usuario.nombre = data.nombre
    usuario.apellido = data.apellido

    db.commit()
    db.refresh(usuario)
    return usuario


# =========================================================
# CAMBIAR CORREO
# =========================================================
@router.put("/correo", response_model=UsuarioOut)
def actualizar_correo(
        data: UsuarioUpdateCorreo,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Actualiza el correo electrónico del usuario.

    Al cambiar el correo, el usuario queda como no verificado.
    """
    # 🔹 Verificar correo único
    if db.query(Usuario).filter(
        Usuario.correo == data.correo,
        Usuario.id != user.id
    ).first():
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    usuario = db.get(Usuario, user.id)
    usuario.correo = data.correo
    usuario.verificado = False  # 🔐 fuerza reverificación

    db.commit()
    db.refresh(usuario)
    return usuario


# =========================================================
# CAMBIAR TELÉFONO
# =========================================================
@router.put("/telefono", response_model=UsuarioOut)
def actualizar_telefono(
        data: UsuarioUpdateTelefono,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Actualiza el número telefónico del usuario autenticado.
    """
    usuario = db.get(Usuario, user.id)
    usuario.telefono = data.telefono

    db.commit()
    db.refresh(usuario)
    return usuario


# =========================================================
# CAMBIAR password
# =========================================================
@router.put("/password")
def actualizar_password(
        data: UsuarioUpdatePassword,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Actualiza la contraseña del usuario.

    Requiere validar la contraseña actual antes del cambio.
    """
    usuario = db.get(Usuario, user.id)

    # 🔐 Verificar password actual
    if not verify_password(data.password_actual, usuario.password):
        raise HTTPException(status_code=400, detail="password actual incorrecta")

    usuario.password = get_password_hash(data.password_nueva)

    db.commit()
    return {"detail": "password actualizada correctamente"}


@router.get("/me", response_model=UsuarioOut)
def get_me(
    user: CurrentUser = Security(get_current_user),
    db: Session = Depends(get_db)
):
    usuario = db.get(Usuario, user.id)

    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuario no encontrado"
        )

    return usuario