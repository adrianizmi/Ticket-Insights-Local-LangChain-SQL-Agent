"""Bounded execution of read-only queries against the ticket database."""

import sqlite3
from pathlib import Path

from ticket_insights.database import connect_readonly

DEFAULT_ROW_LIMIT = 50
PROGRESS_CALLBACK_INTERVAL = 1_000
MAX_PROGRESS_CALLBACKS = 100
SENSITIVE_COLUMNS = {"text"}

BLOCKED_ACTIONS = {
    sqlite3.SQLITE_INSERT,
    sqlite3.SQLITE_UPDATE,
    sqlite3.SQLITE_DELETE,
    sqlite3.SQLITE_ATTACH,
    sqlite3.SQLITE_DETACH,
    sqlite3.SQLITE_ALTER_TABLE,
    sqlite3.SQLITE_CREATE_INDEX,
    sqlite3.SQLITE_CREATE_TABLE,
    sqlite3.SQLITE_CREATE_TEMP_INDEX,
    sqlite3.SQLITE_CREATE_TEMP_TABLE,
    sqlite3.SQLITE_CREATE_TEMP_TRIGGER,
    sqlite3.SQLITE_CREATE_TEMP_VIEW,
    sqlite3.SQLITE_CREATE_TRIGGER,
    sqlite3.SQLITE_CREATE_VIEW,
    sqlite3.SQLITE_CREATE_VTABLE,
    sqlite3.SQLITE_DROP_INDEX,
    sqlite3.SQLITE_DROP_TABLE,
    sqlite3.SQLITE_DROP_TEMP_INDEX,
    sqlite3.SQLITE_DROP_TEMP_TABLE,
    sqlite3.SQLITE_DROP_TEMP_TRIGGER,
    sqlite3.SQLITE_DROP_TEMP_VIEW,
    sqlite3.SQLITE_DROP_TRIGGER,
    sqlite3.SQLITE_DROP_VIEW,
    sqlite3.SQLITE_DROP_VTABLE,
    sqlite3.SQLITE_PRAGMA,
    sqlite3.SQLITE_REINDEX,
    sqlite3.SQLITE_ANALYZE,
    sqlite3.SQLITE_TRANSACTION,
    sqlite3.SQLITE_SAVEPOINT,
}


class TicketQueryError(ValueError):
    """The query does not comply with the tool's read-only contract."""


def ticket_query_authorizer(
    action_code: int,
    argument_1: str | None,
    argument_2: str | None,
    database_name: str | None,
    trigger_name: str | None,
) -> int:
    """Allow ticket reads and deny unauthorized operations."""
    del database_name, trigger_name

    if action_code in BLOCKED_ACTIONS:
        return sqlite3.SQLITE_DENY

    if action_code == sqlite3.SQLITE_READ:
        if argument_1 != "tickets" or argument_2 in SENSITIVE_COLUMNS:
            return sqlite3.SQLITE_DENY

    return sqlite3.SQLITE_OK


def execute_ticket_query(
    database_path: Path,
    sql: str,
    *,
    row_limit: int = DEFAULT_ROW_LIMIT,
) -> list[dict[str, object]]:
    """Run one read-only SELECT or WITH query against tickets."""
    if row_limit < 1:
        raise ValueError("row_limit must be at least 1.")

    normalized_sql = sql.strip()
    first_keyword = normalized_sql.split(maxsplit=1)[0].upper() if normalized_sql else ""
    if first_keyword not in {"SELECT", "WITH"}:
        raise TicketQueryError("Only read-only SELECT or WITH queries are allowed.")

    connection = connect_readonly(database_path=database_path)
    progress_calls_remaining = MAX_PROGRESS_CALLBACKS

    def stop_expensive_query() -> int:
        nonlocal progress_calls_remaining
        progress_calls_remaining -= 1
        return int(progress_calls_remaining <= 0)

    try:
        connection.set_authorizer(ticket_query_authorizer)
        connection.set_progress_handler(stop_expensive_query, PROGRESS_CALLBACK_INTERVAL)
        rows = connection.execute(normalized_sql).fetchmany(row_limit)
        return [{column_name: row[column_name] for column_name in row.keys()} for row in rows]
    except sqlite3.Error as error:
        if progress_calls_remaining <= 0:
            raise TicketQueryError("The query exceeded the execution limit.") from error
        raise TicketQueryError(f"The query was rejected or is invalid: {error}") from error
    finally:
        connection.close()
