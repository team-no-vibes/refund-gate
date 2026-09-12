"""The one door to the outside world, and the log that proves what went through it."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

from lib.types import canonical

LOG = Path("log/adapter.jsonl")
WITHHELD = {"status": "proposed_not_executed"}


def read_only() -> bool:
    """One env var decides whether writes leave the process."""
    return os.environ.get("AGENT_READ_ONLY") == "1"


class Adapter:
    """Wraps a transport with read_events() and post(payload); logs every call."""

    def __init__(self, transport, log_path: str | Path = LOG) -> None:
        self.transport = transport
        self.log_path = Path(log_path)

    def _record(self, method: str, args: object) -> None:
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "method": method,
            "args_hash": hashlib.sha256(canonical(args).encode("utf-8")).hexdigest(),
        }
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(canonical(entry) + "\n")

    def read_events(self) -> list:
        self._record("read_events", None)
        return self.transport.read_events()

    def post(self, payload: dict) -> dict:
        """Logged first, so a withheld write leaves the same trail as a real one."""
        self._record("post", payload)
        if read_only():
            return dict(WITHHELD)
        return self.transport.post(payload)


def log_lines(log_path: str | Path = LOG) -> list[dict]:
    path = Path(log_path)
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
