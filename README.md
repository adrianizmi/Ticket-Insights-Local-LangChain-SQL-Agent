# Ticket Insights: Local LangChain SQL Agent

A local-first LangChain agent that answers natural-language questions about support
tickets using secure, read-only SQLite tools. The repository also includes a
structured-output ticket classifier and a reproducible agent evaluation suite.

## Highlights

- Runs locally with Ollama and `qwen3:4b-instruct`; no API key is required.
- Uses LangChain tools for deterministic ticket counting, schema inspection, and
  read-only SQL queries.
- Enforces SQLite authorization, a row limit, and an execution limit.
- Blocks access to ticket bodies through the SQL agent.
- Evaluates the agent against eight reproducible data and safety cases: **8/8 passed**.
- Includes a Pydantic-validated classifier for six ticket categories.

## Architecture

```text
Natural-language question
        |
        v
LangChain agent + local Ollama model
        |
        v
Read-only Python tools
        |
        v
SQLite authorization layer -> tickets database
```

The model selects tools and turns tool results into an answer. Python and SQLite
enforce the data-access policy; the model cannot grant itself more permissions.

## Quick start

Requirements:

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Docker Desktop with Docker Compose

```bash
git clone <your-repository-url>
cd ticket-insights
uv sync --locked --extra ai
docker compose up -d
```

The first Docker run downloads `qwen3:4b-instruct` (approximately 2.5 GB). Check
that it is ready:

```bash
docker compose logs --follow ollama-model
docker compose exec ollama ollama list
```

Create the demo database and inspect its deterministic summary:

```bash
uv run ticket-insights init-db
uv run ticket-insights summary
```

Ask the agent a question:

```bash
uv run --extra ai ticket-insights ask "How many open access tickets are there?"
```

Classify an incoming ticket:

```bash
uv run --extra ai ticket-insights classify "I cannot sign in and receive a 403 error."
```

Run the agent evaluation:

```bash
uv run --extra ai python -m ticket_insights.evaluation
```

The included configuration achieved 8/8 passing cases with `qwen3:4b-instruct`.
Local inference time depends on the host machine.

## Security and privacy

- Ollama is bound to `127.0.0.1` by Docker Compose.
- The application accepts only loopback Ollama endpoints by default. Set
  `ALLOW_REMOTE_OLLAMA=true` only when you explicitly authorize sending ticket data
  to a remote endpoint.
- SQL tools allow only `SELECT` and `WITH` queries against the `tickets` table.
- SQLite blocks writes, schema changes, attachments, PRAGMA statements, and access to
  the ticket `text` column.
- Query results are limited to 50 rows and expensive queries are interrupted.

All bundled records are fictional. Do not treat this demo as a production access
control system for real customer data without authentication, authorization,
redaction, audit logging, and a broader security review.

## Quality checks

```bash
uv run --extra ai pytest
uv run --extra ai ruff check src tests
uv run --extra ai ruff format --check src tests
```

The test suite does not call Ollama. Agent evaluation is intentionally separate
because it runs local model inference.

## Repository layout

```text
.
├── compose.yaml                 Local Ollama service and model download
├── data/                        Fictional fixtures and evaluation cases
├── examples/                    Standalone direct-model example
├── src/ticket_insights/
│   ├── agent.py                 LangChain agent configuration
│   ├── classifier.py            Structured ticket classification
│   ├── evaluation.py            Reproducible agent evaluation
│   ├── sql.py                   Read-only query policy and execution limits
│   └── tools.py                 LangChain tool definitions
└── tests/                       Offline unit tests
```

## Current scope

The SQL agent is ready as a local, verifiable portfolio demonstration. The classifier
returns validated predictions but does not persist them or include an accuracy
evaluation yet. Future work could add a separate prediction table and evaluate the
classifier against a larger, representative dataset.

## License

Choose and add a license before publishing. MIT is a suitable default for this
portfolio project.
