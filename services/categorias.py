from sqlalchemy.orm import Session
from models.categoria import Categoria, TipoMovimientoEnum
from constants.categorias_default import (
    CATEGORIAS_INGRESO_DEFAULT,
    CATEGORIAS_EGRESO_DEFAULT
)

def crear_categorias_default(usuario_id: str, db: Session):
    categorias = []

    for nombre in CATEGORIAS_INGRESO_DEFAULT:
        categorias.append(
            Categoria(
                usuario_id=usuario_id,
                nombre=nombre,
                tipo_movimiento=TipoMovimientoEnum.Ingreso
            )
        )

    for nombre in CATEGORIAS_EGRESO_DEFAULT:
        categorias.append(
            Categoria(
                usuario_id=usuario_id,
                nombre=nombre,
                tipo_movimiento=TipoMovimientoEnum.Egreso
            )
        )

    db.add_all(categorias)
