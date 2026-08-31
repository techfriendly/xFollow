from __future__ import annotations

from pathlib import Path
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from .config import load_runtime_config, repo_root

_DB_READY: bool | None = None
_DB_ERROR: str | None = None


def schema_paths() -> list[Path]:
    return sorted((repo_root() / "infra" / "postgres").glob("*.sql"))


def connection():
    config = load_runtime_config()
    if config.force_memory:
        raise RuntimeError("xfollow_memory_forced")
    if not config.postgres_dsn:
        raise RuntimeError("postgres_dsn_not_configured")
    return psycopg2.connect(config.postgres_dsn, connect_timeout=config.db_connect_timeout, cursor_factory=RealDictCursor)


def migrate_schema() -> dict[str, object]:
    global _DB_READY, _DB_ERROR
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(hashtext('xfollow:schema'))")
        for path in schema_paths():
            cursor.execute(path.read_text(encoding="utf-8"))
        cursor.execute("SELECT version FROM xfollow.schema_migrations ORDER BY version")
        versions = [row["version"] for row in cursor.fetchall()]
        conn.commit()
    _DB_READY = True
    _DB_ERROR = None
    return {"status": "ok", "schema": "xfollow", "migrations": versions}


def db_available() -> bool:
    global _DB_READY, _DB_ERROR
    if _DB_READY is True:
        return _DB_READY
    try:
        migrate_schema()
    except Exception as exc:
        _DB_READY = False
        _DB_ERROR = str(exc)
    return _DB_READY


def status() -> dict[str, object]:
    config = load_runtime_config()
    if config.force_memory:
        return {"backend": "memory", "connected": False, "required": config.db_required, "schema": "xfollow", "error": "xfollow_memory_forced"}
    if db_available():
        return {"backend": "postgres", "connected": True, "required": config.db_required, "schema": "xfollow", "error": None}
    return {"backend": "postgres", "connected": False, "required": config.db_required, "schema": "xfollow", "error": _DB_ERROR or "database_unavailable"}


def reset_db_probe() -> None:
    global _DB_READY, _DB_ERROR
    _DB_READY = None
    _DB_ERROR = None


def fetch_all(query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def fetch_one(query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
    with connection() as conn, conn.cursor() as cursor:
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None
