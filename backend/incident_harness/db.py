"""Engine/session setup. Real PostgreSQL when INCIDENT_DATABASE_URL
points at one and is reachable; otherwise a real on-disk SQLite
database, the same fallback ai-governance-audit-readiness-register
and model-validation-alerting use, so a repo that names PostgreSQL in
its stack does not silently mean "SQLite always" or crash outright
when Postgres is not standing as a service on this machine."""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base

_DEFAULT_SQLITE_URL = "sqlite:///incident_harness.db"


def _resolve_database_url() -> str:
    return os.environ.get("INCIDENT_DATABASE_URL", _DEFAULT_SQLITE_URL)


def postgres_is_configured() -> bool:
    url = os.environ.get("INCIDENT_DATABASE_URL", "")
    return url.startswith("postgresql")


def postgres_is_reachable(database_url: str | None = None) -> bool:
    """Best-effort connectivity probe used only to decide whether a
    Postgres-specific test should run or skip; never raises."""
    url = database_url or os.environ.get("INCIDENT_DATABASE_URL", "")
    if not url.startswith("postgresql"):
        return False
    try:
        probe_engine = create_engine(url, connect_args={"connect_timeout": 2})
        with probe_engine.connect():
            pass
        probe_engine.dispose()
        return True
    except Exception:
        return False


def make_engine(database_url: str | None = None):
    url = database_url or _resolve_database_url()
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


def make_session_factory(engine=None) -> sessionmaker:
    engine = engine or make_engine()
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def init_schema(engine) -> None:
    Base.metadata.create_all(engine)
