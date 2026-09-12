#!/usr/bin/env bash
set -euo pipefail
command -v sha256sum >/dev/null 2>&1 || sha256sum() { shasum -a 256 "$@"; }
cd "$(git rev-parse --show-toplevel)"
RED() { echo "RED $1"; exit 1; }; GREEN() { echo "GREEN $1"; }

stage=-1; [ -s MANIFEST ] && stage=$(tail -n1 MANIFEST | cut -d, -f1); next=$((stage+1))
echo "ratified_stage=$stage building_stage=$next"

allowed=$(awk -v max="$next" '/^## stage /{s=$3+0} /^allow:/{if (s<=max){sub(/^allow: */,"");print}}' STAGES.md | tr ' ' '\n' | grep -v '^$' | sort -u || true)
[ -n "$allowed" ] || RED "stages:no-allow-lines-up-to-stage-$next"
while IFS= read -r f; do
  ok=0
  while IFS= read -r a; do
    case "$a" in */) case "$f" in "$a"*) ok=1 ;; esac ;; *) [ "$f" = "$a" ] && ok=1 ;; esac
  done <<< "$allowed"
  [ "$ok" -eq 1 ] || RED "allowlist:$f"
done <<< "$(git ls-files)"
GREEN allowlist

git ls-files | grep -qiE '^(STATUS|PROGRESS|REPORT|NOTES)\.md$' && RED "narrative_file" || true
GREEN no_narrative

git ls-files | grep -v '^ci/' | xargs -r grep -lnE '(sk-or-|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY)' 2>/dev/null && RED "secret_pattern" || true
GREEN no_secrets

src=$(git ls-files 'lib/*.py' 'bin/*' || true)
[ -n "$src" ] && { echo "$src" | xargs grep -lnE '\b(TODO|FIXME|mock|placeholder)\b' 2>/dev/null && RED "placeholder" || true; }
GREEN no_placeholders

tst=$(git ls-files 'tests/*.py' || true)
[ -n "$tst" ] && { echo "$tst" | xargs grep -lnE 'requests\.|urllib|httpx|socket\.' 2>/dev/null && RED "network_in_tests" || true; }
GREEN no_network_in_tests

cap=$(awk -F= '/^bound: loc_cap=/{print $2}' STAGES.md)
base=$(git rev-parse -q --verify origin/main 2>/dev/null || true)
if [ -n "$base" ]; then
  adds=$(git diff --numstat "$base" HEAD | awk '{a+=$1} END{print a+0}'); echo "loc:+$adds"
  [ "$adds" -le "$cap" ] || RED "loc_cap:+$adds"
fi
GREEN loc_cap

if [ -n "$base" ]; then
  for c in $(git rev-list --no-merges "$base"..HEAD); do
    git log -1 --format=%B "$c" | grep -q '^Model: ' || RED "trailer_model:$c"
    git log -1 --format=%B "$c" | grep -q '^Task: ' || RED "trailer_task:$c"
  done
fi
GREEN trailers

if [ -s MANIFEST ]; then
  n=0; prev=""
  while IFS= read -r line || [ -n "$line" ]; do
    n=$((n+1)); IFS=, read -r st tree key date sig chain <<< "$line"
    [ "$st" = "$((n-1))" ] || RED "manifest:line$n:order"
    [ "${sig#SIGNED_OFF_BY=}" != "$sig" ] || RED "manifest:line$n:signature"
    if [ -n "$prev" ]; then want=$(printf '%s' "$prev" | sha256sum | cut -d' ' -f1); [ "$chain" = "chain=$want" ] || RED "manifest:line$n:chain"; fi
    git cat-file -e "${tree}^{tree}" 2>/dev/null || RED "manifest:line$n:tree"
    prev="$line"
  done < MANIFEST
fi
GREEN manifest

[ -n "$tst" ] && python -m pytest -q tests >/dev/null 2>&1 || { [ -z "$tst" ] || RED "pytest"; }
GREEN tests
echo "GREEN all"
