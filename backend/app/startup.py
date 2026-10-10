"""DB init and seed admin user."""

from __future__ import annotations

import time

from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.core.security import hash_password
from app.db.models import User
from app.db.session import Base, SessionLocal, engine


def wait_for_db(retries: int = 30, delay: float = 1.0) -> None:
    for i in range(retries):
        try:
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            return
        except OperationalError:
            time.sleep(delay)
    raise RuntimeError("Database not reachable")


def init_db() -> None:
    wait_for_db()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == settings.admin_email.lower()).first()
        if not admin:
            admin = User(
                email=settings.admin_email.lower(),
                full_name=settings.admin_name,
                hashed_password=hash_password(settings.admin_password),
                is_admin=True,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print(f"Seeded admin user: {settings.admin_email}")
        else:
            # Ensure admin flag
            if not admin.is_admin:
                admin.is_admin = True
                db.commit()
    finally:
        db.close()
