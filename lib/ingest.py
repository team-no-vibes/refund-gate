"""Turn an inbound message into a RefundRequest. Parsing only: no network, no Slack SDK."""

from __future__ import annotations

import re

from lib.types import RefundRequest

ORDER = re.compile(r"\bORD-\d+\b")
CUSTOMER = re.compile(r"\bC-\d+\b")
MONEY = re.compile(r"\$\s?([\d,]+(?:\.\d{2})?)")
REASON = re.compile(r"\s+[-–—:]\s+")


def _token(pattern: re.Pattern, text: str, field: str) -> str:
    found = pattern.search(text)
    if not found:
        raise ValueError(f"message text carries no {field}")
    return found.group(0)


def _cents(text: str) -> int:
    """Integer arithmetic only, so $129.99 can never round to 12998."""
    found = MONEY.search(text)
    if not found:
        raise ValueError("message text carries no amount")
    whole, _, frac = found.group(1).replace(",", "").partition(".")
    return int(whole) * 100 + int((frac + "00")[:2])


def _reason(text: str) -> str:
    """Everything after the first dash or colon is the customer's own words."""
    parts = REASON.split(text, maxsplit=1)
    if len(parts) != 2 or not parts[1].strip():
        raise ValueError("message text carries no reason")
    return parts[1].strip()


def slack(event: dict) -> RefundRequest:
    text = event["text"]
    return RefundRequest(
        customer_id=_token(CUSTOMER, text, "customer id"),
        order_id=_token(ORDER, text, "order id"),
        amount_cents=_cents(text),
        reason=_reason(text),
        msg_ts=event["ts"],
    )
