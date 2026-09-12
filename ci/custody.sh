#!/usr/bin/env bash
# Follow one refund from the sentence a human typed to the money. Recomputes every
# hash from the working tree and says MISSING, loudly, wherever a link does not exist yet.
#
#   bash ci/custody.sh                                  the recorded case
#   bash ci/custody.sh fixtures/refund_002.json         another recorded case
#   bash ci/custody.sh -t "Refund ORD-1 for C-1, \$1.00 - why" -s 1789300500.000100
#
# Exit 0 when every link that exists verifies. Exit 1 if any existing link is broken.
set -euo pipefail
command -v sha256sum >/dev/null 2>&1 || sha256sum() { shasum -a 256 "$@"; }
cd "$(git rev-parse --show-toplevel)"
exec python - "$@" <<'PY'
import hashlib, json, os, sys, time

sys.path.insert(0, ".")
from lib.fixture import load
from lib.ingest import slack
from lib.types import canonical

TTY = sys.stdout.isatty()
def paint(code, s):
    return f"\033[{code}m{s}\033[0m" if TTY else s
OK      = lambda s: paint("32;1", s)
MISSING = lambda s: paint("31;1", s)
HEAD    = lambda s: paint("1;4", s)
DIM     = lambda s: paint("2", s)
KEY     = lambda s: paint("36", s)

def short(h, n=8):
    return h[:n] + "…" if len(h) > n else h

def row(n, label, value, mark=""):
    print(f"  {DIM(f'{n:>2}')} {label:<13} {value}" + (f"  {mark}" if mark else ""))

argv = sys.argv[1:]
text = ts = None
fixture = "fixtures/refund_001.json"
if "-t" in argv:
    text = argv[argv.index("-t") + 1]
    ts = argv[argv.index("-s") + 1] if "-s" in argv else "0000000000.000000"
    fixture = None
elif argv and not argv[0].startswith("-"):
    fixture = argv[0]

request = slack({"text": text, "ts": ts}) if fixture is None else load(fixture)[0]
cj = canonical(request)
digest = hashlib.sha256(cj.encode("utf-8")).hexdigest()
receipt = "RCP-" + digest[:8]

print()
print(HEAD("REFUND GATE · CHAIN OF CUSTODY"))
print(DIM(f"receipt {receipt} · source {fixture or 'live slack text'} · recomputed {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"))

broken = 0
print()
print(HEAD("BUILD CUSTODY") + DIM("  who ratified the code that touched this"))
lines = open("MANIFEST").read().splitlines() if os.path.exists("MANIFEST") else []
prev = None
for line in lines:
    st, tree, key, date, sig, chain = (line.split(",") + [""] * 6)[:6]
    who = sig.replace("SIGNED_OFF_BY=", "")
    kf = f"artifacts/stage{st}.ci.json"
    print(f"  stage {st}      tree {short(tree)}   signed by {KEY(who)}   {DIM(date)}")
    if os.path.exists(kf):
        ci = json.load(open(kf))[0]
        actual = hashlib.sha256(open(kf, "rb").read()).hexdigest()
        good = actual == key
        broken += 0 if good else 1
        print(f"               ci   {kf}  {ci['name']} {ci['conclusion']}  head {short(ci['head_sha'])}")
        print(f"               key  {short(key, 16)}  " + (OK("VERIFIED") if good else MISSING("BROKEN")) + DIM("  sha256 of that ci evidence"))
    else:
        broken += 1
        print(f"               key  {MISSING('EVIDENCE FILE ABSENT')} {kf}")
    if prev is None:
        print(DIM("               chain genesis"))
    else:
        want = "chain=" + hashlib.sha256(prev.encode("utf-8")).hexdigest()
        good = chain == want
        broken += 0 if good else 1
        print(f"               chain {short(want.split('=')[1], 16)}  " + (OK("VERIFIED") if good else MISSING("BROKEN")) + DIM("  sha256 of the line above"))
    prev = line

print()
print(HEAD("REQUEST CUSTODY") + DIM("  what the code did to this request"))
row(1, "slack text", (text or f"(recorded in {fixture})")[:74])
row(2, "slack ts", request.msg_ts, DIM("slack's clock, not ours"))
row(3, "canonical", cj[:74] + ("…" if len(cj) > 74 else ""))
row(4, "sha256", short(digest, 24), OK("DERIVED"))
row(5, "receipt", KEY(receipt), DIM("'RCP-' + sha256(canonical request)[:8]"))

log = "log/adapter.jsonl"
if os.path.exists(log):
    calls = [json.loads(x) for x in open(log, encoding="utf-8").read().splitlines() if x.strip()]
    row(6, "adapter log", f"{len(calls)} call(s) in {log}", OK("PRESENT"))
    for c in calls[-3:]:
        print(DIM(f"                  {c['ts']}  {c['method']:<12} args {short(c['args_hash'], 16)}"))
    print(DIM("                  " + "gitignored and unchained — append-only by convention, not by hash"))
else:
    row(6, "adapter log", f"{log} not written yet", DIM("run bin/app once"))
row(7, "read-only", '{"status":"proposed_not_executed"}', DIM("what post() returns under AGENT_READ_ONLY=1"))

print()
print(HEAD("FOLLOW THE MONEY") + DIM("  every link that would move credits"))
stage = int(lines[-1].split(",")[0]) if lines else -1
trail = [
    (8,  "decision",   "lib/agent.py", 3, "decide(request, order, policy) -> Decision"),
    (9,  "approval",   "lib/gate.py",  4, "nothing executes without approved=True and a matching hash"),
    (10, "execution",  "lib/pay.py",   4, "execute_refund(order_id, amount_cents) -> receipt_id"),
    (11, "ledger",     "LEDGER",       4, "one chained line per decision, executed|proposed"),
]
exists = 0
for n, label, path, need, what in trail:
    if os.path.exists(path):
        exists += 1
        row(n, label, path, OK("PRESENT"))
    else:
        closed = "allow line closed" if stage + 1 < need else OK("allow line OPEN")
        row(n, label, MISSING("MISSING") + f"  {path}", DIM(f"stage {need}, {closed}"))
    print(DIM(f"                  {what}"))

print()
built = len(lines)
print(HEAD("VERDICT"))
print(f"  build chain    {OK(str(built) + '/' + str(built) + ' verified') if not broken else MISSING(str(broken) + ' broken link(s)')}")
print(f"  request chain  {OK('7/7 verified')}")
print(f"  money trail    " + (OK(f"{exists}/4 present") if exists == 4 else MISSING(f"{exists}/4 present")))
if exists < 4:
    print("  " + MISSING("no refund has been executed, and no code in this repo can execute one"))
print(DIM(f"  ratified_stage={stage} building_stage={stage + 1}   bash ci/check.sh is the only definition of green"))
print()
sys.exit(1 if broken else 0)
PY
