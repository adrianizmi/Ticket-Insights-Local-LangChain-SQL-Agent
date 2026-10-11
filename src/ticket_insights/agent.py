from pathlib import Path

from langchain.agents import create_agent

from ticket_insights.model import create_chat_model
from ticket_insights.tools import (
    create_count_tickets_tool,
    create_ticket_query_tool,
    create_ticket_schema_tool,
)

SYSTEM_PROMPT = """
Answer in English.
For every request that requires ticket data, you MUST call a tool before answering.
Never write a tool call, SQL query, or result as plain text: use the native tool call.
Do not invent columns, SQL, or results. Inspect the schema if you do not know the
available columns. Preserve every explicit filter in the question.

Use count_matching_tickets ONLY when the request asks for the number of tickets with
both a specific category and status. Its only filters are category and status; never
pass a product or omit either filter. For example, for "How many open access tickets
are there?", call count_matching_tickets(category="access", status="open").

Use query_ticket_data for every other data request: totals, aggregations, products,
dates, or searches with no matches. Always use simple lowercase aliases in
aggregations, such as `COUNT(*) AS count`.
Examples:
- Total: SELECT COUNT(*) AS count FROM tickets
- By category: SELECT category, COUNT(*) AS count FROM tickets GROUP BY category
  ORDER BY category
- Product with the most open tickets: SELECT product, COUNT(*) AS count FROM tickets
  WHERE status = 'open' GROUP BY product ORDER BY count DESC, product ASC LIMIT 1

Explain the data concisely. Your final answer must be based exclusively on the last
tool result. If it returns an empty list, say that no tickets match the filters; never
invent identifiers or rows. If a required column is missing, explain which data is
missing. Explicitly refuse requests to insert, change, or delete data. If a tool
returns an error, correct the query or explain the limit.
"""


def create_ticket_agent(database_path: Path):
    model = create_chat_model()

    tools = [
        create_count_tickets_tool(database_path=database_path),
        create_ticket_query_tool(database_path=database_path),
        create_ticket_schema_tool(database_path=database_path),
    ]

    return create_agent(
        model=model,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
