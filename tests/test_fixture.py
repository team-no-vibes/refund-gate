import pytest

from lib.fixture import fixture_hash, load
from lib.types import OrderRecord, Policy, RefundRequest

ONE = "fixtures/refund_001.json"
TWO = "fixtures/refund_002.json"


def test_load_returns_the_three_records():
    req, order, policy = load(ONE)
    assert isinstance(req, RefundRequest)
    assert isinstance(order, OrderRecord)
    assert isinstance(policy, Policy)


def test_the_recorded_case_is_what_was_recorded():
    req, order, policy = load(ONE)
    assert (req.customer_id, req.order_id, req.amount_cents) == ("C-4471", "ORD-20913", 12999)
    assert req.msg_ts == "1789300500.000100"
    assert (order.days_since_purchase, order.status) == (11, "delivered")
    assert policy.window_days == 30
    assert policy.source_url == "https://www.electronicexpress.com/return-policy"
    assert "within 30 days" in policy.text


def test_the_escalating_case_is_outside_the_window_and_over_the_threshold():
    _, order, policy = load(TWO)
    assert order.days_since_purchase > policy.window_days
    assert order.amount_cents > policy.escalate_over_cents


def test_notes_in_the_json_do_not_reach_the_policy_record():
    _, _, policy = load(ONE)
    assert not hasattr(policy, "escalate_over_cents_source")


def test_fixture_hash_is_stable_across_calls():
    assert fixture_hash(ONE) == fixture_hash(ONE)


def test_fixture_hash_separates_the_two_cases():
    assert fixture_hash(ONE) != fixture_hash(TWO)


def test_a_fixture_missing_a_field_is_an_error(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"message":{},"order":{},"policy":{}}', encoding="utf-8")
    with pytest.raises(ValueError):
        load(str(bad))
