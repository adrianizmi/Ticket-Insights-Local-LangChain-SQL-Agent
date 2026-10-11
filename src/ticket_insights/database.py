"""Demo database creation and explicit read-only access."""

import csv
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL,
    product TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('open', 'in_progress', 'closed')),
    text TEXT NOT NULL,
    category TEXT NOT NULL CHECK (
        category IN ('access', 'billing', 'performance', 'bug', 'feature', 'other')
    )
);
"""


def create_demo_database(database_path: Path, fixture_path: Path) -> int:
    """Create a new database without replacing an existing one."""
    with fixture_path.open(encoding="utf-8", newline="") as fixture:
        reader = csv.DictReader(fixture)
        expected = {"id", "created_at", "product", "status", "text", "category"}
        if set(reader.fieldnames or []) != expected:
            raise ValueError(
                "The CSV must contain id, created_at, product, status, text, and category."
            )
        rows = list(reader)
    if not rows:
        raise ValueError("The demo CSV is empty.")

    database_path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents replacement even when two processes race.
    with database_path.open("xb"):
        pass
    try:
        connection = sqlite3.connect(database_path)
        try:
            with connection:
                connection.execute(SCHEMA)
                connection.executemany(
                    """INSERT INTO tickets (id, created_at, product, status, text, category)
                       VALUES (:id, :created_at, :product, :status, :text, :category)""",
                    rows,
                )
        finally:
            connection.close()
    except Exception:
        database_path.unlink(missing_ok=True)
        raise
    return len(rows)


def connect_readonly(database_path: Path) -> sqlite3.Connection:
    """Open an existing database without allowing writes.

    The caller must close the connection. A `with connection` block controls
    transactions, but does not automatically close sqlite3 connections.
    """
    connection = sqlite3.connect(database_path.resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def get_summary(database_path: Path) -> dict[str, object]:
    """Return a deterministic local summary without calling an LLM."""
    connection = connect_readonly(database_path)
    try:
        total = connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        statuses = connection.execute(
            "SELECT status, COUNT(*) AS count FROM tickets GROUP BY status ORDER BY status"
        ).fetchall()
        return {"total": total, "by_status": {row["status"]: row["count"] for row in statuses}}
    finally:
        connection.close()
