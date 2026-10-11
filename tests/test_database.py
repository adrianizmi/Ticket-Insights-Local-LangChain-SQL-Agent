import json
import sqlite3
from pathlib import Path

import pytest

from ticket_insights.cli import main
from ticket_insights.database import connect_readonly, create_demo_database, get_summary

FIXTURE = Path(__file__).resolve().parents[1] / "data" / "sample_tickets.csv"


@pytest.fixture
def database(tmp_path):
    path = tmp_path / "tickets.db"
    create_demo_database(path, FIXTURE)
    return path


def test_demo_summary(database):
    assert get_summary(database) == {
        "total": 12,
        "by_status": {"closed": 4, "in_progress": 2, "open": 6},
    }


def test_initialization_never_overwrites_existing_database(database):
    original = database.read_bytes()
    with pytest.raises(FileExistsError):
        create_demo_database(database, FIXTURE)
    assert database.read_bytes() == original


def test_missing_database_is_not_created(tmp_path):
    path = tmp_path / "missing.db"
    with pytest.raises(sqlite3.OperationalError):
        connect_readonly(path)
    assert not path.exists()


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM tickets",
        "UPDATE tickets SET status = 'closed'",
        "DROP TABLE tickets",
    ],
)
def test_readonly_connection_blocks_writes(database, sql):
    connection = connect_readonly(database)
    try:
        with pytest.raises(sqlite3.OperationalError):
            connection.execute(sql)
        assert connection.execute("SELECT COUNT(*) FROM tickets").fetchone()[0] == 12
    finally:
        connection.close()


def test_invalid_fixture_does_not_leave_partial_database(tmp_path):
    fixture = tmp_path / "invalid.csv"
    fixture.write_text(
        "id,created_at,product,status,text,category\n1,2026-10-01,Atlas,unknown,Ejemplo,access\n",
        encoding="utf-8",
    )
    path = tmp_path / "invalid.db"
    with pytest.raises(sqlite3.IntegrityError):
        create_demo_database(path, fixture)
    assert not path.exists()


def test_invalid_csv_headers_do_not_create_database(tmp_path):
    fixture = tmp_path / "invalid.csv"
    fixture.write_text("id,text\n1,Ejemplo\n", encoding="utf-8")
    path = tmp_path / "invalid.db"
    with pytest.raises(ValueError, match="CSV"):
        create_demo_database(path, fixture)
    assert not path.exists()


def test_cli_init_and_summary(tmp_path, capsys):
    path = tmp_path / "cli.db"
    assert main(["init-db", "--db", str(path), "--fixture", str(FIXTURE)]) == 0
    assert "12 fictional tickets" in capsys.readouterr().out
    assert main(["summary", "--db", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["total"] == 12


def test_cli_missing_database_returns_actionable_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        main(["summary", "--db", str(tmp_path / "missing.db")])
    assert error.value.code == 1
    assert "Error:" in capsys.readouterr().err
