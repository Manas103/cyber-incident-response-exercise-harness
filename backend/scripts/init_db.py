"""Stands up the schema (and seeds fixed reference data plus the demo
official runs) against whatever database INCIDENT_DATABASE_URL points
at, or the local SQLite fallback."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from incident_harness.api import create_app  # noqa: E402

if __name__ == "__main__":
    app = create_app()
    print(f"schema ready at {app.state.engine.url}")
