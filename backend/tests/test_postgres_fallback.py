"""PostgreSQL is not installed as a service on this machine (see README
and CLAUDE.md's toolchain notes). This test only runs the real-Postgres
path when INCIDENT_DATABASE_URL is set to a postgresql:// URL and that
database is actually reachable; otherwise it skips cleanly rather than
failing, and a second test confirms the SQLite fallback path (the one
every other test in this suite already exercises) is what create_app
actually uses by default."""

import os

import pytest

from incident_harness.api import create_app
from incident_harness.db import postgres_is_reachable


@pytest.mark.skipif(
    not postgres_is_reachable(),
    reason="INCIDENT_DATABASE_URL is not set to a reachable PostgreSQL instance on this machine",
)
def test_schema_stands_up_against_real_postgres():
    app = create_app(database_url=os.environ["INCIDENT_DATABASE_URL"], seed=False)
    app.state.engine.dispose()


def test_default_database_url_is_sqlite_when_no_postgres_url_is_configured():
    from incident_harness.db import _resolve_database_url

    saved = os.environ.pop("INCIDENT_DATABASE_URL", None)
    try:
        assert _resolve_database_url().startswith("sqlite")
    finally:
        if saved is not None:
            os.environ["INCIDENT_DATABASE_URL"] = saved
