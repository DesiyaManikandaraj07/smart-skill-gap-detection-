"""Ensure DB schema exists before API tests."""

from app.startup import init_db

init_db()
