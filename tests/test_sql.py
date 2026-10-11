from pathlib import Path

import pytest

from ticket_insights.database import create_demo_database
from ticket_insights.sql import TicketQueryError, execute_ticket_query

FIXTURE = Path(__file__).resolve().parents[1] / "data" / "sample_tickets.csv"


@pytest.fixture
def database(tmp_path: Path) -> Path:
    path = tmp_path / "tickets.db"
    create_demo_database(path, FIXTURE)
    return path


def test_query_returns_structured_rows_and_respects_row_limit(database: Path) -> None:
    result = execute_ticket_query(
        database,
        "SELECT id, category, status FROM tickets ORDER BY id",
        row_limit=2,
    )

    assert result == [
        {"id": 1, "category": "access", "status": "open"},
        {"id": 2, "category": "billing", "status": "closed"},
    ]


def test_query_returns_empty_list_when_no_rows_match(database: Path) -> None:
    result = execute_ticket_query(
        database,
        "SELECT id FROM tickets WHERE category = 'unknown'",
    )

    assert result == []


def test_query_rejects_unknown_columns(database: Path) -> None:
    with pytest.raises(TicketQueryError, match="rejected or is invalid"):
        execute_ticket_query(database, "SELECT nonexistent_column FROM tickets")


def test_query_rejects_access_to_other_tables(database: Path) -> None:
    with pytest.raises(TicketQueryError, match="rejected or is invalid"):
        execute_ticket_query(database, "SELECT name FROM sqlite_master")


def test_query_rejects_ticket_text_to_avoid_exposing_ticket_content(
    database: Path,
) -> None:
    with pytest.raises(TicketQueryError, match="rejected or is invalid"):
        execute_ticket_query(database, "SELECT text FROM tickets")


def test_query_rejects_writes_and_preserves_data(database: Path) -> None:
    with pytest.raises(TicketQueryError, match="Only read-only"):
        execute_ticket_query(database, "DELETE FROM tickets")

    result = execute_ticket_query(database, "SELECT COUNT(*) AS total FROM tickets")
    assert result == [{"total": 12}]


def test_query_rejects_attach(database: Path) -> None:
    with pytest.raises(TicketQueryError, match="Only read-only"):
        execute_ticket_query(database, "ATTACH DATABASE ':memory:' AS other")


def test_query_stops_expensive_queries(database: Path) -> None:
    with pytest.raises(TicketQueryError, match="execution limit"):
        execute_ticket_query(
            database,
            """
            SELECT COUNT(*) AS total
            FROM tickets AS first
            CROSS JOIN tickets AS second
            CROSS JOIN tickets AS third
            CROSS JOIN tickets AS fourth
            CROSS JOIN tickets AS fifth
            CROSS JOIN tickets AS sixth
            """,
        )
