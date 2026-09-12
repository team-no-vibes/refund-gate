# STAGES, the build contract. Amended only by the human.
bound: loc_cap=300

## stage 0 harness
allow: artifacts/ ci/ STAGES.md MANIFEST CLAIMS.md GROUND_TRUTH.md .github/ .gitignore README.md pyproject.toml tests/
spec: ci/check.sh and ci/ratify.sh from the kickoff, plus one line after set -euo pipefail in both: command -v sha256sum >/dev/null 2>&1 || sha256sum() { shasum -a 256 "$@"; }. README line one is `bash ci/check.sh`. pyproject: python 3.12, pytest only. tests/test_smoke.py asserts True. CLAIMS.md format: task_id,model,stage,status.
exit: bash ci/check.sh prints GREEN all here and CI green on the pushed branch

## stage 1 fixture and types
allow: lib/types.py lib/fixture.py fixtures/ tests/test_types.py tests/test_fixture.py
spec: lib/types.py, frozen dataclasses: RefundRequest(customer_id, order_id, amount_cents, reason, msg_ts), OrderRecord(order_id, amount_cents, days_since_purchase, status), Policy(window_days, escalate_over_cents, text, source_url), Decision(action, amount_cents, reasons, hash). Canonical JSON everywhere: json.dumps(sort_keys=True, separators=(",",":")). fixtures/refund_001.json holds one recorded Slack message, one order, one policy (text and source_url from Exa, pasted by hand). lib/fixture.py load(path) returns (RefundRequest, OrderRecord, Policy) and fixture_hash(path) returns sha256 of canonical JSON of the three.
exit: check green; fixture_hash called twice returns the same value

## stage 2 adapter
allow: lib/adapter.py tests/test_adapter.py
spec: class Adapter(transport). transport is any object with read_events() and post(payload). Adapter.read_events() and Adapter.post(payload) append one line to log/adapter.jsonl: {ts, method, args_hash}. If env AGENT_READ_ONLY is 1, post() sends nothing and returns {"status":"proposed_not_executed"}. Tests use a RecordedTransport that replays fixtures/refund_001.json. The Slack transport (CopilotKit Channels) lives in bin/ at stage 4, never in lib/.
exit: check green; test_adapter runs with zero network and asserts the read-only branch

## stage 3 the agent
allow: lib/agent.py bin/agent tests/test_agent.py GOLDEN
spec: lib/agent.py decide(request, order, policy) -> Decision. Pure, no model call, no clock. Order of checks: escalate if amount_cents > order.amount_cents or amount_cents > policy.escalate_over_cents; else deny if days_since_purchase > window_days or status != "delivered"; else refund. reasons is a list of the rule names that fired. Decision.hash = sha256 of canonical JSON of {request, order, window_days, escalate_over_cents, action, amount_cents, reasons}; policy text and any timestamps excluded. bin/agent <fixture> prints the Decision JSON then a last line HASH <hash>; bin/agent --golden <fixture> writes the hash to GOLDEN. Why the channel matters: the refund is proposed in the Slack channel where support and the manager already work, and the decision is a receipt the manager can replay, not a chat answer.
exit: check green; test_agent asserts bin/agent on refund_001 equals GOLDEN; two clean checkouts agree on GOLDEN

## stage 4 the gate
allow: lib/gate.py lib/pay.py bin/gate tests/test_gate.py LEDGER
spec: lib/pay.py execute_refund(order_id, amount_cents) -> receipt_id, a stub returning sha256(order_id + amount_cents)[:12], no network. lib/gate.py gate(decision, adapter, approval) where approval is {approver_sub, decision_hash, approved}. Nothing executes without approved=True and decision_hash equal to decision.hash. On execute or on read-only, append one line to LEDGER: decision_hash,approver_sub,utc_ts,executed|proposed,chain=sha256(previous line). AGENT_READ_ONLY=1 always writes proposed and never calls execute_refund. bin/gate wires the Slack approval card (CopilotKit Channels) and Auth0 CIBA, which supplies approver_sub; network only here.
exit: check green; test_gate verifies the LEDGER chain, asserts execute_refund is not called under AGENT_READ_ONLY=1, and asserts a hash mismatch never executes
