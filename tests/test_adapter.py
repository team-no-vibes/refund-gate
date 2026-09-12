"""Replay only. RecordedTransport is the whole transport; nothing here opens a connection."""

import json

from lib.adapter import WITHHELD, Adapter, log_lines

FIXTURE = "fixtures/refund_001.json"
CARD = {"channel": "C-REFUNDS", "text": "refund requested"}


class RecordedTransport:
    """Replays the recorded Slack message and remembers what was posted to it."""

    def __init__(self, path=FIXTURE):
        with open(path, encoding="utf-8") as fh:
            self.blob = json.load(fh)
        self.posted = []

    def read_events(self):
        return [self.blob["message"]]

    def post(self, payload):
        self.posted.append(payload)
        return {"ok": True, "ts": self.blob["message"]["msg_ts"]}


def adapter(tmp_path):
    transport = RecordedTransport()
    return Adapter(transport, tmp_path / "adapter.jsonl"), transport


def test_read_events_replays_the_recorded_message(tmp_path):
    a, _ = adapter(tmp_path)
    events = a.read_events()
    assert [e["order_id"] for e in events] == ["ORD-20913"]


def test_post_reaches_the_transport_and_returns_its_result(tmp_path, monkeypatch):
    monkeypatch.delenv("AGENT_READ_ONLY", raising=False)
    a, transport = adapter(tmp_path)
    assert a.post(CARD)["ok"] is True
    assert transport.posted == [CARD]


def test_read_only_withholds_the_write(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_READ_ONLY", "1")
    a, transport = adapter(tmp_path)
    assert a.post(CARD) == WITHHELD
    assert transport.posted == []


def test_a_withheld_write_still_leaves_a_line(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_READ_ONLY", "1")
    a, _ = adapter(tmp_path)
    a.post(CARD)
    assert [e["method"] for e in log_lines(tmp_path / "adapter.jsonl")] == ["post"]


def test_every_call_is_logged_in_order(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_READ_ONLY", "1")
    a, _ = adapter(tmp_path)
    a.read_events()
    a.post(CARD)
    entries = log_lines(tmp_path / "adapter.jsonl")
    assert [e["method"] for e in entries] == ["read_events", "post"]
    assert all(sorted(e) == ["args_hash", "method", "ts"] for e in entries)
    assert all(len(e["args_hash"]) == 64 for e in entries)


def test_the_args_hash_separates_two_different_payloads(tmp_path, monkeypatch):
    monkeypatch.setenv("AGENT_READ_ONLY", "1")
    a, _ = adapter(tmp_path)
    a.post(CARD)
    a.post(CARD)
    a.post({"channel": "C-REFUNDS", "text": "something else"})
    first, second, third = (e["args_hash"] for e in log_lines(tmp_path / "adapter.jsonl"))
    assert first == second != third


def test_no_log_file_reads_back_as_no_calls(tmp_path):
    assert log_lines(tmp_path / "absent.jsonl") == []
