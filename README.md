bash ci/check.sh

That command is the only definition of green. It runs as the pre-commit hook, in CI,
and inside every model's loop before it may claim anything. It prints `GREEN <name>`
or `RED <name>` and exits at the first RED.

STAGES.md is the build contract: each stage lists the only files that may exist at
that stage, what to build, and what green means. Only the human amends it.

A stage is ratified only when a human runs `ci/ratify.sh <stage> <name>` at a terminal.
It refuses to run in CI, re-runs the check, fetches the CI record for the exact commit,
hashes it, and appends one line to MANIFEST chained to the previous line's hash.

`AGENT_READ_ONLY=1` makes the agent observe and propose without acting.

Setup:

    python3.12 -m venv .venv && .venv/bin/pip install pytest && source .venv/bin/activate
    printf '#!/bin/sh\nexec "$(git rev-parse --show-toplevel)/ci/check.sh"\n' > .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit ci/*.sh
