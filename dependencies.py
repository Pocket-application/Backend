import os
from fastapi import Depends, HTTPException, status, Request
from jose import jwt, JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import SessionLocal

security = HTTPBearer()

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]

class CurrentUser:
    def __init__(self, id: str, rol: str):
        self.id = id
        self.rol = rol


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """
    Dependencia para obtener el usuario actual desde el JWT.

    Valida el token, verifica expiración y guarda el usuario en request.state
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True}  # verifica expiración
        )

        user = CurrentUser(
            id=payload["sub"],
            rol=payload.get("rol", "user")
        )

        # 🔗 Guardar usuario en request.state para middleware
        request.state.user = user

        return user

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )