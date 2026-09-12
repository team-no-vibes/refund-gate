"""Parsing only, zero network. The fixture is the truth; the test declares the wire format."""

import pytest

from lib.fixture import load
from lib.ingest import slack
from lib.types import canonical

RECORDED = "fixtures/refund_001.json"
TEXT = "Refund ORD-20913 for C-4471, $129.99 - bought the wrong tier, credits unused"
TS = "1789300500.000100"


def test_a_typed_message_parses_to_the_recorded_request():
    assert canonical(slack({"text": TEXT, "ts": TS})) == canonical(load(RECORDED)[0])


def test_the_timestamp_comes_from_the_event_not_the_text():
    assert slack({"text": TEXT, "ts": "1789399999.000999"}).msg_ts == "1789399999.000999"


@pytest.mark.parametrize(
    "amount,cents",
    [("$489.00", 48900), ("$12.00", 1200), ("$1,299.99", 129999), ("$129.99", 12999), ("$7", 700)],
)
def test_amounts_land_on_exact_cents(amount, cents):
    text = f"Refund ORD-1 for C-1, {amount} - changed my mind"
    assert slack({"text": text, "ts": TS}).amount_cents == cents


@pytest.mark.parametrize("sep", [" - ", " — ", " – ", " : "])
def test_any_dash_or_colon_opens_the_reason(sep):
    text = f"Refund ORD-1 for C-1, $1.00{sep}credits unused"
    assert slack({"text": text, "ts": TS}).reason == "credits unused"


@pytest.mark.parametrize(
    "text",
    [
        "Refund for C-4471, $129.99 - no order id here",
        "Refund ORD-20913, $129.99 - no customer id here",
        "Refund ORD-20913 for C-4471 - no amount here",
        "Refund ORD-20913 for C-4471, $129.99",
    ],
)
def test_a_message_missing_a_field_is_not_a_refund_request(text):
    with pytest.raises(ValueError):
        slack({"text": text, "ts": TS})
