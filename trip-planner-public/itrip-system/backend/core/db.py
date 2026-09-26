# backend/core/db.py
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

DATABASE_URL = URL.create(
    "postgresql+psycopg2",
    username=settings.pg_user,
    password=settings.pg_password,
    host=settings.pg_host,
    port=settings.pg_port,
    database=settings.pg_db,
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"connect_timeout": settings.pg_connect_timeout},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
