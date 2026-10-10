"""SQLAlchemy engine and session factory."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


_connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
_engine_kwargs: dict = {"pool_pre_ping": True, "connect_args": _connect_args}
if not settings.database_url.startswith("sqlite"):
    _engine_kwargs.update({"pool_size": 5, "max_overflow": 10})

engine = create_engine(settings.database_url, **_engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
