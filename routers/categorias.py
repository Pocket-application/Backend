from fastapi import APIRouter, Depends, Security, HTTPException
from sqlalchemy.orm import Session

from models.categoria import Categoria
from schemas.categoria import CategoriaCreate, CategoriaUpdate, CategoriaOut
from dependencies import get_current_user, CurrentUser, get_db

router = APIRouter(
    prefix="/categorias",
    tags=["Categorias"]
)

# =========================================================
# CREAR CATEGORÍA
# =========================================================
@router.post("/", response_model=CategoriaOut)
def crear_categoria(
        data: CategoriaCreate,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Crea una nueva categoría financiera para el usuario autenticado.

    Cada categoría es única por usuario y puede clasificar
    movimientos de tipo Ingreso, Egreso o Ambos.

    Errores:
    -------
    400 Bad Request
        Si la categoría ya existe para el usuario.
    """
    # 🔹 Evitar duplicados por usuario
    if db.query(Categoria).filter(
        Categoria.usuario_id == user.id,
        Categoria.nombre == data.nombre
    ).first():
        raise HTTPException(status_code=400, detail="La categoría ya existe")

    categoria = Categoria(
        usuario_id=user.id,
        nombre=data.nombre,
        tipo_movimiento=data.tipo_movimiento
    )
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


# =========================================================
# LISTAR CATEGORÍAS DEL USUARIO
# =========================================================
@router.get("/", response_model=list[CategoriaOut])
def listar_categorias(
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Lista todas las categorías pertenecientes al usuario autenticado.

    Las categorías se retornan ordenadas alfabéticamente por nombre.
    """
    return (
        db.query(Categoria)
        .filter(Categoria.usuario_id == user.id)
        .order_by(Categoria.nombre)
        .all()
    )


# =========================================================
# ACTUALIZAR CATEGORÍA
# =========================================================
@router.put("/{categoria_id}", response_model=CategoriaOut)
def actualizar_categoria(
        categoria_id: int,
        data: CategoriaUpdate,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Actualiza el nombre y/o tipo de movimiento de una categoría.

    Solo permite modificar categorías que pertenezcan al usuario.

    Errores:
    -------
    404 Not Found
        Si la categoría no existe o no pertenece al usuario.
    """
    categoria = db.query(Categoria).filter(
        Categoria.id == categoria_id,
        Categoria.usuario_id == user.id
    ).first()

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    if data.nombre is not None:
        categoria.nombre = data.nombre

    if data.tipo_movimiento is not None:
        categoria.tipo_movimiento = data.tipo_movimiento

    db.commit()
    db.refresh(categoria)
    return categoria


# =========================================================
# ELIMINAR CATEGORÍA
# =========================================================
@router.delete("/{categoria_id}")
def eliminar_categoria(
        categoria_id: int,
        user: CurrentUser = Security(get_current_user),
        db: Session = Depends(get_db)
    ):
    """
    Elimina una categoría del usuario autenticado.

    No permite eliminar categorías que estén referenciadas
    por movimientos financieros.
    """
    categoria = db.query(Categoria).filter(
        Categoria.id == categoria_id,
        Categoria.usuario_id == user.id
    ).first()

    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    db.delete(categoria)
    db.commit()

    return {"detail": "Categoría eliminada correctamente"}
