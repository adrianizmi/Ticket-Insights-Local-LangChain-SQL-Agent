from pathlib import Path

import pytest

from ticket_insights.analytics import count_tickets
from ticket_insights.database import create_demo_database

FIXTURE = Path(__file__).resolve().parents[1] / "data" / "sample_tickets.csv"


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "tickets.db"
    create_demo_database(path, FIXTURE)
    return path


@pytest.mark.parametrize(
    ("category", "status", "expected"),
    [
        ("access", "open", 2),
        ("access", "in_progress", 1),
        ("feature", "open", 0),
        ("unknown", "open", 0),
        ("acces' OR 1=1 --", "open", 0),
    ],
)
def test_count_tickets_with_different_filters(database, category, status, expected):
    result = count_tickets(database_path=database, category=category, status=status)
    assert result == expected
