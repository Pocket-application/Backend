import os
from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from database import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]

# ==========================
# DB DEPENDENCY
# ==========================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================
# SECURITY
# ==========================
class CurrentUser:
    def __init__(self, id: str, rol: str):
        self.id = id
        self.rol = rol

def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return CurrentUser(payload["sub"], payload["rol"])
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

def require_role(*roles: str):
    def checker(user: CurrentUser = Depends(get_current_user)):
        if user.rol not in roles:
            raise HTTPException(status_code=403, detail="Permiso denegado")
        return user
    return checker
