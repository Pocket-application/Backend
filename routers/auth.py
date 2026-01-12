from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models.usuario import Usuario
from models.refresh_token import RefreshToken
from schemas.auth import LoginRequest, TokenResponse, RefreshRequest, LogoutRequest
from security_tokens import verify_password, create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    """
    Autentica a un usuario y genera tokens de acceso.

    Valida las credenciales del usuario (correo y contraseña).
    Si son correctas, genera:
    - Un access token (JWT de corta duración)
    - Un refresh token (persistido en base de datos)

    Endpoint público.

    Parámetros:
    ----------
    data : LoginRequest
        Credenciales del usuario (correo y contraseña).

    Retorna:
    -------
    TokenResponse
        Objeto con access_token y refresh_token.

    Errores:
    -------
    401 Unauthorized
        Si las credenciales son inválidas.
    """
    db = SessionLocal()
    user = db.query(Usuario).filter(Usuario.correo == data.correo).first()

    if not user or not verify_password(data.password, user.password): # type: ignore
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access = create_access_token(user.id, user.rol) # type: ignore
    refresh, exp = create_refresh_token(user.id) # type: ignore

    db.add(RefreshToken(usuario_id=user.id, token=refresh, expira=exp))
    db.commit()

    return {"access_token": access, "refresh_token": refresh}


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(data: RefreshRequest):
    """
    Renueva el access token usando un refresh token válido.
    """
    db = SessionLocal()

    # 🔍 Buscar refresh token válido
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == data.refresh_token
    ).first()

    if not db_token:
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    # ⏰ Verificar expiración
    if db_token.expira < datetime.now(timezone.utc): # type: ignore
        db.delete(db_token)
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token expirado")

    user = db.query(Usuario).filter(
        Usuario.id == db_token.usuario_id
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no válido")

    # 🔁 ROTACIÓN (nivel pro)
    db.delete(db_token)

    new_access = create_access_token(user.id, user.rol) # type: ignore
    new_refresh, exp = create_refresh_token(user.id) # type: ignore

    db.add(
        RefreshToken(
            usuario_id=user.id,
            token=new_refresh,
            expira=exp
        )
    )

    db.commit()

    return {
        "access_token": new_access,
        "refresh_token": new_refresh
    }
    
@router.post("/logout")
def logout(data: LogoutRequest):
    """
    Cierra la sesión del usuario eliminando el refresh token.
    """
    db = SessionLocal()

    token = db.query(RefreshToken).filter(
        RefreshToken.token == data.refresh_token
    ).first()

    if token:
        db.delete(token)
        db.commit()

    # 🔒 Respuesta neutra (no revela información)
    return {"detail": "Sesión cerrada correctamente"}