from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from core.settings import settings

DATABASE_URL = settings.database_url
DB_SCHEMA = settings.db_schema

class Base(DeclarativeBase):
    pass

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "options": f"-csearch_path={DB_SCHEMA}"
    }
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)
