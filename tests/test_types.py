import dataclasses
import json

import pytest

from lib.types import Decision, OrderRecord, Policy, RefundRequest, canonical


def test_the_four_records_have_exactly_the_fields_stages_names():
    assert [f.name for f in dataclasses.fields(RefundRequest)] == [
        "customer_id", "order_id", "amount_cents", "reason", "msg_ts"]
    assert [f.name for f in dataclasses.fields(OrderRecord)] == [
        "order_id", "amount_cents", "hours_since_purchase", "status"]
    assert [f.name for f in dataclasses.fields(Policy)] == [
        "window_hours", "escalate_over_cents", "text", "source_url"]
    assert [f.name for f in dataclasses.fields(Decision)] == [
        "action", "amount_cents", "reasons", "hash"]


def test_records_are_frozen():
    order = OrderRecord("ORD-1", 100, 1, "delivered")
    with pytest.raises(dataclasses.FrozenInstanceError):
        order.amount_cents = 999


def test_canonical_sorts_keys_and_drops_whitespace():
    assert canonical({"b": 1, "a": 2}) == '{"a":2,"b":1}'


def test_canonical_of_a_record_is_its_fields():
    order = OrderRecord("ORD-1", 100, 1, "delivered")
    assert json.loads(canonical(order)) == {
        "order_id": "ORD-1", "amount_cents": 100,
        "hours_since_purchase": 1, "status": "delivered"}


def test_equal_records_encode_to_the_same_bytes():
    a = OrderRecord("ORD-1", 100, 1, "delivered")
    b = OrderRecord("ORD-1", 100, 1, "delivered")
    assert canonical(a) == canonical(b)
