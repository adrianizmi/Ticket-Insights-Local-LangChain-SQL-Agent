from pathlib import Path

from langchain.tools import tool

from ticket_insights.analytics import count_tickets
from ticket_insights.database import connect_readonly
from ticket_insights.sql import TicketQueryError, execute_ticket_query


def create_count_tickets_tool(database_path: Path):
    @tool
    def count_matching_tickets(category: str, status: str) -> int:
        """Count tickets with an exact category and status.

        Use this when the request asks for a ticket count and specifies both category
        and status. Preserve both filters exactly as they appear in the request.
        """
        return count_tickets(
            database_path=database_path,
            category=category,
            status=status,
        )

    return count_matching_tickets


def create_ticket_schema_tool(database_path: Path):
    @tool
    def get_tickets_schema() -> list[dict[str, str]]:
        """Return the available columns and types in the tickets table."""
        connection = connect_readonly(database_path=database_path)

        try:
            columns = connection.execute("""PRAGMA table_info(tickets)""").fetchall()

            result = []

            for column in columns:
                result.append(
                    {
                        "name": column["name"],
                        "type": column["type"],
                    }
                )
        finally:
            connection.close()
        return result

    return get_tickets_schema


def create_ticket_query_tool(database_path: Path):
    @tool
    def query_ticket_data(sql: str) -> list[dict[str, object]] | dict[str, str]:
        """Run a read-only SELECT or WITH query against tickets.

        Use this for aggregations or filters that count_matching_tickets cannot
        express. Do not use it to count one specific category and status. It cannot
        read ticket bodies. Inspect the schema when columns are unknown. It returns at
        most 50 rows and rejects writes and access to other tables.
        """
        try:
            return execute_ticket_query(database_path, sql)
        except TicketQueryError as error:
            return {"error": str(error)}

    return query_ticket_data
