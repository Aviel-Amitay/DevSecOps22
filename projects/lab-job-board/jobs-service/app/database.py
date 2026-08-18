import os
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


def database_url():
    """Build the connection URL, preferring an explicitly supplied URL.

    In containers the password is mounted as a Docker secret, keeping it out of
    both the Compose file and the container environment.
    """
    if value := os.getenv("DATABASE_URL"):
        return value

    password_file = Path(
        os.getenv("POSTGRES_PASSWORD_FILE", "/run/secrets/db_password")
    )
    if password_file.is_file():
        password = password_file.read_text(encoding="utf-8").strip()
    else:
        password = os.getenv("POSTGRES_PASSWORD")
        if not password:
            raise RuntimeError(
                "Set DATABASE_URL or provide POSTGRES_PASSWORD_FILE"
            )

    user = quote_plus(os.getenv("POSTGRES_USER", "postgres"))
    password = quote_plus(password)
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    name = os.getenv("POSTGRES_DB", "jobboard")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


DATABASE_URL = database_url()

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
