"""Minimal CLI that exposes only implemented functionality."""

import argparse
import json
import sqlite3
from pathlib import Path

from ticket_insights.database import create_demo_database, get_summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Explore fictional support tickets with SQLite.")
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init-db", help="Create a database from the demo tickets.")
    init.add_argument("--db", type=Path, default=Path("data/tickets.db"))
    init.add_argument("--fixture", type=Path, default=Path("data/sample_tickets.csv"))

    summary = commands.add_parser("summary", help="Show the total and status breakdown.")
    summary.add_argument("--db", type=Path, default=Path("data/tickets.db"))

    ask = commands.add_parser("ask", help="Ask the local agent about tickets.")
    ask.add_argument("question", help="Natural-language question.")
    ask.add_argument("--db", type=Path, default=Path("data/tickets.db"))

    classify = commands.add_parser("classify", help="Classify a ticket with the local model.")
    classify.add_argument("ticket", help="Ticket text to classify.")

    args = parser.parse_args(argv)
    try:
        if args.command == "init-db":
            count = create_demo_database(args.db, args.fixture)
            print(f"Created demo database at {args.db}: {count} fictional tickets.")
        elif args.command == "summary":
            print(json.dumps(get_summary(args.db), ensure_ascii=False, indent=2))
        elif args.command == "ask":
            from ticket_insights.agent import create_ticket_agent

            agent = create_ticket_agent(args.db)
            result = agent.invoke(
                {"messages": [{"role": "user", "content": args.question}]},
                {"recursion_limit": 6},
            )
            tool_messages = [message for message in result["messages"] if message.type == "tool"]
            print(result["messages"][-1].content)
            if tool_messages:
                print("\nTool evidence:")
                for message in tool_messages:
                    print(f"- {message.name}: {message.content}")
        else:
            from ticket_insights.classifier import classify_ticket
            from ticket_insights.model import create_chat_model

            prediction = classify_ticket(create_chat_model(), args.ticket)
            print(prediction.model_dump_json(indent=2))
    except FileExistsError:
        parser.exit(1, "Error: the database already exists. Use --db with a new path.\n")
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f"Error: {error}\n")
    return 0
