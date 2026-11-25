import hashlib
import os
from contextlib import contextmanager
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"


@contextmanager
def connect():
    with psycopg.connect(host="db", dbname=os.environ.get("AGENTBOARD_DATABASE", "agentboard"),
                         user="agentboard", password=Path("/run/secrets/db_password").read_text().strip(),
                         row_factory=dict_row, connect_timeout=5) as conn:
        yield conn


def migrate():
    with connect() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(625015)")
        conn.execute("CREATE TABLE IF NOT EXISTS schema_versions (version text PRIMARY KEY, checksum text NOT NULL)")
        for file in sorted(MIGRATIONS.glob("*.sql")):
            sql = file.read_bytes()
            checksum = hashlib.sha256(sql).hexdigest()
            old = conn.execute("SELECT checksum FROM schema_versions WHERE version=%s", (file.name,)).fetchone()
            if old:
                if old["checksum"] != checksum:
                    raise RuntimeError(f"Applied migration changed: {file.name}")
                continue
            conn.execute(sql.decode())
            conn.execute("INSERT INTO schema_versions VALUES (%s,%s)", (file.name, checksum))
