"""Read a recorded refund case off disk. No network, ever: the replay reads the file."""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields

from lib.types import OrderRecord, Policy, RefundRequest, canonical


def _build(cls, blob: dict):
    """Keep only the fields the dataclass declares, so notes in the JSON are inert."""
    names = [f.name for f in fields(cls)]
    missing = [n for n in names if n not in blob]
    if missing:
        raise ValueError(f"{cls.__name__} missing {missing}")
    return cls(**{n: blob[n] for n in names})


def load(path: str) -> tuple[RefundRequest, OrderRecord, Policy]:
    with open(path, encoding="utf-8") as fh:
        blob = json.load(fh)
    return (
        _build(RefundRequest, blob["message"]),
        _build(OrderRecord, blob["order"]),
        _build(Policy, blob["policy"]),
    )


def fixture_hash(path: str) -> str:
    payload = canonical([canonical(rec) for rec in load(path)])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
