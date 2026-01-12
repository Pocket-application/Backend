from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from core.settings import settings

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = int(settings.access_token_expire_minutes)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_access_token(user_id: str, rol: str) -> str:
    """
    Crea un JWT de acceso con tiempo de expiración seguro (timestamp UTC en segundos)
    """
    expire = datetime.now(tz=timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    expire_ts = int(expire.timestamp()) 
    payload = {"sub": user_id, "rol": rol, "exp": expire_ts}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> tuple[str, datetime]:
    """
    Crea un refresh token de larga duración (30 días)
    """
    expire = datetime.now(tz=timezone.utc) + timedelta(days=30)
    expire_ts = int(expire.timestamp())
    payload = {"sub": user_id, "exp": expire_ts}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM), expire
