"""Local, validated classification of support tickets."""

from typing import Literal

from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field, field_validator

TicketCategory = Literal[
    "access",
    "billing",
    "performance",
    "bug",
    "feature",
    "other",
]


class TicketClassification(BaseModel):
    """Validated prediction that does not change the reference label."""

    category: TicketCategory
    summary: str = Field(min_length=1, max_length=160)

    @field_validator("summary")
    @classmethod
    def summary_must_contain_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("summary cannot be empty.")
        return value.strip()


SYSTEM_PROMPT = """
Classify a ticket into one of these categories: access, billing, performance, bug,
feature, or other. Use other when the text does not allow a confident category.
Write a short, impersonal summary based only on the ticket. Do not invent product,
status, dates, causes, or solutions.
"""


def classify_ticket(model: ChatOllama, ticket_text: str) -> TicketClassification:
    """Classify a ticket using structured output from the local model."""
    classifier = model.with_structured_output(TicketClassification)
    return classifier.invoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", ticket_text),
        ]
    )
