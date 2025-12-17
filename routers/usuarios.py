from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.usuario import UsuarioCreate, UsuarioOut
from models.usuario import Usuario
from security import get_password_hash
from dependencies import get_db
from utils.id_generator import generate_unique_user_id

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.post("/", response_model=UsuarioOut)
def registrar_usuario(data: UsuarioCreate, db: Session = Depends(get_db)):
    
    # Verificar correo único
    if db.query(Usuario).filter(Usuario.correo == data.correo).first():
        raise HTTPException(status_code=400, detail="Correo ya registrado")

    # Generar ID único
    user_id = generate_unique_user_id(db)

    user = Usuario(
        id=user_id,
        nombre=data.nombre,
        apellido=data.apellido,
        correo=data.correo,
        contraseña=get_password_hash(data.password),
        rol="user"
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
