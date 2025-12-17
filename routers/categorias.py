from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models.categoria import Categoria
from schemas.categoria import CategoriaCreate, CategoriaOut
from dependencies import get_current_user

router = APIRouter(
    prefix="/categorias",
    tags=["Categorias"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=CategoriaOut)
def crear_categoria(data: CategoriaCreate, user=Depends(get_current_user)):
    db: Session = SessionLocal()
    categoria = Categoria(
        usuario_id=user.id,
        nombre=data.nombre,
        tipo_movimiento=data.tipo_movimiento
    )
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria

@router.get("/", response_model=list[CategoriaOut])
def listar_categorias(user=Depends(get_current_user)):
    db: Session = SessionLocal()
    return db.query(Categoria).filter(Categoria.usuario_id == user.id).all()
