from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models.usuario import Usuario
from models.refresh_token import RefreshToken
from schemas.auth import LoginRequest, TokenResponse
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

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access = create_access_token(user.id, user.rol)
    refresh, exp = create_refresh_token(user.id)

    db.add(RefreshToken(usuario_id=user.id, token=refresh, expira=exp))
    db.commit()

    return {"access_token": access, "refresh_token": refresh}
