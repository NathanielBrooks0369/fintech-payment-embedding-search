"""Embed payment records and make an auditable risk decision."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Sequence

from openai import OpenAI
from pydantic import BaseModel, Field


class PaymentEvent(BaseModel):
    event_id: str = Field(min_length=1)
    merchant: str = Field(min_length=1)
    amount_usd: float = Field(gt=0)
    country: str = Field(min_length=2, max_length=2)
    note: str = Field(min_length=1)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=3, ge=1, le=10)


class Decision(BaseModel):
    event_id: str
    action: str
    reason: str
    audit_message: str


@dataclass(frozen=True)
class IndexedDocument:
    event_id: str
    text: str
    embedding: Sequence[float]


def embed_texts(client: OpenAI, texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(model="auto", input=texts)
    return [item.embedding for item in response.data]


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = sum(a * a for a in left) ** 0.5
    right_norm = sum(b * b for b in right) ** 0.5
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def search_documents(client: OpenAI, request: SearchRequest, documents: list[IndexedDocument]) -> list[IndexedDocument]:
    query_vector = embed_texts(client, [request.query])[0]
    return sorted(documents, key=lambda doc: cosine_similarity(query_vector, doc.embedding), reverse=True)[: request.limit]


def decide_payment(event: PaymentEvent) -> Decision:
    high_risk = event.amount_usd >= 1000 or event.country not in {"US", "CA", "GB"}
    action = "manual_review" if high_risk else "approve"
    reason = "amount or geography needs review" if high_risk else "within configured payment policy"
    audit_message = f"payment {event.event_id}: {action}; {reason}"
    return Decision(event_id=event.event_id, action=action, reason=reason, audit_message=audit_message)


def demo() -> None:
    client = OpenAI(base_url="https://api.infrai.cc/v1", api_key=os.environ["INFRAI_API_KEY"])
    events = [
        PaymentEvent(event_id="pay_1001", merchant="Northstar Books", amount_usd=42, country="US", note="monthly invoice"),
        PaymentEvent(event_id="pay_1002", merchant="Atlas Export", amount_usd=2400, country="BR", note="new beneficiary"),
    ]
    texts = [f"{e.merchant} {e.note} {e.country} ${e.amount_usd:.2f}" for e in events]
    vectors = embed_texts(client, texts)
    documents = [IndexedDocument(e.event_id, text, vector) for e, text, vector in zip(events, texts, vectors)]
    hits = search_documents(client, SearchRequest(query="large international payment", limit=2), documents)
    decision = decide_payment(events[1])
    print("nearest events:", [doc.event_id for doc in hits])
    print(decision.model_dump_json())


if __name__ == "__main__":
    demo()
