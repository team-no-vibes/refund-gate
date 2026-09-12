"""The four records the refund gate passes around, and the one JSON encoding."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RefundRequest:
    customer_id: str
    order_id: str
    amount_cents: int
    reason: str
    msg_ts: str


@dataclass(frozen=True)
class OrderRecord:
    order_id: str
    amount_cents: int
    hours_since_purchase: int
    status: str


@dataclass(frozen=True)
class Policy:
    window_hours: int
    escalate_over_cents: int
    text: str
    source_url: str


@dataclass(frozen=True)
class Decision:
    action: str
    amount_cents: int
    reasons: tuple[str, ...]
    hash: str


def canonical(value: object) -> str:
    """The only JSON encoding in this repo. Byte-identical for equal values."""
    if hasattr(value, "__dataclass_fields__"):
        value = asdict(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
