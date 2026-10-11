from pathlib import Path

from ticket_insights.database import connect_readonly


def count_tickets(database_path: Path, *, category: str, status: str) -> int:
    """Count tickets that exactly match a category and status."""
    connection = connect_readonly(database_path=database_path)

    try:
        total_tickets = connection.execute(
            """
            SELECT COUNT(*) FROM tickets
            WHERE category = ? AND status = ?
            """,
            (category, status),
        ).fetchone()[0]
    finally:
        connection.close()
    return total_tickets
