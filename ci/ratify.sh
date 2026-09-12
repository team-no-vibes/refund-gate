#!/usr/bin/env bash
set -euo pipefail
command -v sha256sum >/dev/null 2>&1 || sha256sum() { shasum -a 256 "$@"; }
cd "$(git rev-parse --show-toplevel)"
die() { echo "ratify: $1"; exit 1; }
[ -t 0 ] || die "interactive terminal required"
[ -z "${CI:-}" ] || die "refuses to run in CI"
st="${1:?usage: ratify.sh <stage>}"; who="${2:?usage: ratify.sh <stage> <your-name>}"
bash ci/check.sh
cur=-1; [ -s MANIFEST ] && cur=$(tail -n1 MANIFEST | cut -d, -f1)
[ "$st" -gt "$cur" ] || die "stage $st already ratified"
tree=$(git rev-parse "HEAD^{tree}"); sha=$(git rev-parse HEAD)
mkdir -p artifacts
gh api "repos/{owner}/{repo}/commits/$sha/check-runs" --jq '[.check_runs[] | {name, head_sha, conclusion, completed_at}]' > "artifacts/stage$st.ci.json"
grep -q '"conclusion": *"success"' "artifacts/stage$st.ci.json" || die "no successful CI run for $sha"
key=$(sha256sum "artifacts/stage$st.ci.json" | cut -d' ' -f1)
prev=$(tail -n1 MANIFEST 2>/dev/null || true); chain=""
[ -n "$prev" ] && chain="chain=$(printf '%s' "$prev" | sha256sum | cut -d' ' -f1)"
echo "$st,$tree,$key,$(date -u +%FT%TZ),SIGNED_OFF_BY=$who,$chain" >> MANIFEST
echo "ratified stage $st on tree $tree"
