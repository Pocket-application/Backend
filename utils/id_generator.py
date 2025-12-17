import secrets
from sqlalchemy.orm import Session
from models.usuario import Usuario

HEX_CHARS = "0123456789abcdef"

def generate_unique_user_id(
    db: Session,
    length: int = 7,
    max_attempts: int = 10
) -> str:
    """
    Genera un ID hexadecimal único de longitud fija.
    Verifica unicidad contra la base de datos.
    """

    for _ in range(max_attempts):
        user_id = "".join(secrets.choice(HEX_CHARS) for _ in range(length))

        exists = db.query(Usuario).filter(Usuario.id == user_id).first()
        if not exists:
            return user_id

    raise RuntimeError("No se pudo generar un ID único para el usuario")
