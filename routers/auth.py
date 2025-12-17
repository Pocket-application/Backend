from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models.usuario import Usuario
from models.refresh_token import RefreshToken
from schemas.auth import LoginRequest, TokenResponse
from security import verify_password, create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    db = SessionLocal()
    user = db.query(Usuario).filter(Usuario.correo == data.correo).first()

    if not user or not verify_password(data.password, user.contraseña):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    access = create_access_token(user.id, user.rol)
    refresh, exp = create_refresh_token(user.id)

    db.add(RefreshToken(usuario_id=user.id, token=refresh, expira=exp))
    db.commit()

    return {"access_token": access, "refresh_token": refresh}
