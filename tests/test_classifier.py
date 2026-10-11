import pytest
from pydantic import ValidationError

from ticket_insights.classifier import TicketClassification


def test_classification_accepts_a_supported_category_and_trims_summary() -> None:
    result = TicketClassification(category="access", summary="  Sign-in error.  ")

    assert result.category == "access"
    assert result.summary == "Sign-in error."


@pytest.mark.parametrize(
    ("category", "summary"),
    [
        ("unknown", "Valid text."),
        ("bug", "   "),
    ],
)
def test_classification_rejects_invalid_values(category: str, summary: str) -> None:
    with pytest.raises(ValidationError):
        TicketClassification(category=category, summary=summary)
