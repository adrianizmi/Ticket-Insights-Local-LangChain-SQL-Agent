import json
from pathlib import Path

from ticket_insights.agent import create_ticket_agent

DATABASE_PATH = Path("data/tickets.db")
CASES_PATH = Path("data/sql_cases.json")


def extract_actual_rows(tool_messages):
    data_messages = [
        message
        for message in tool_messages
        if message.name
        in {
            "count_matching_tickets",
            "query_ticket_data",
        }
    ]

    if not data_messages:
        return None

    last_message = data_messages[-1]

    if last_message.name == "count_matching_tickets":
        return [{"count": int(last_message.content)}]

    if isinstance(last_message.content, str):
        return json.loads(last_message.content)

    return last_message.content


def evaluate_expected_behavior(expected_behavior: str, final_answer: str) -> bool:
    answer = final_answer.lower()

    if expected_behavior == "explain_missing_data":
        mentions_resolution = "resolution" in answer
        mentions_missing_data = any(
            phrase in answer
            for phrase in (
                "cannot",
                "not available",
                "does not exist",
                "missing",
            )
        )
        mentions_schema = any(
            phrase in answer
            for phrase in (
                "closed_at",
                "closing date",
                "close date",
                "column",
                "schema",
                "required data",
            )
        )
        return mentions_resolution and mentions_missing_data and mentions_schema

    if expected_behavior == "reject_write":
        return any(phrase in answer for phrase in ("cannot", "not allowed", "unable to")) and any(
            word in answer for word in ("delete", "remove", "modify", "change")
        )

    raise ValueError(f"Unknown evaluation behavior: {expected_behavior}")


def evaluate_sql_cases():
    with CASES_PATH.open(encoding="utf-8") as file:
        cases = json.load(file)

    agent = create_ticket_agent(DATABASE_PATH)
    results = []

    for case in cases:
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": case["question"],
                    }
                ]
            },
            {
                "recursion_limit": 6,
            },
        )

        tool_messages = [message for message in result["messages"] if message.type == "tool"]

        actual_rows = extract_actual_rows(tool_messages)
        expected_rows = case.get("expected_rows")
        final_answer = result["messages"][-1].content

        if expected_rows is not None:
            passed = actual_rows == expected_rows
        else:
            passed = evaluate_expected_behavior(
                case["expected_behavior"],
                final_answer,
            )

        results.append(
            {
                "id": case["id"],
                "question": case["question"],
                "expected_rows": expected_rows,
                "actual_rows": actual_rows,
                "expected_behavior": case.get("expected_behavior"),
                "final_answer": final_answer,
                "passed": passed,
                "tool_messages": tool_messages,
            }
        )

    return results


if __name__ == "__main__":
    results = evaluate_sql_cases()

    for result in results:
        status = "PASS" if result["passed"] else "FAIL"

        print(f"\n{result['id']}: {status}")
        print(f"  Expected: {result['expected_rows']}")
        print(f"  Actual: {result['actual_rows']}")

    passed_cases = sum(result["passed"] for result in results)
    print(f"\nResult: {passed_cases}/{len(results)} cases passed")
