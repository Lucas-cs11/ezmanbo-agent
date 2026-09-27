import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

_db_dir = Path(os.getenv("DATA_DIR", str(Path(__file__).resolve().parent.parent / "data")))
_db_dir.mkdir(parents=True, exist_ok=True)

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL") or f"sqlite:///{_db_dir}/ezmanbo.db"

_connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=_connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from . import models_db  # noqa: ensure all models are registered
    Base.metadata.create_all(bind=engine)
