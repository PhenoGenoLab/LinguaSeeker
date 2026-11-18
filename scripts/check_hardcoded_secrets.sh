#!/usr/bin/env bash
# Fail when a change introduces a hardcoded secret literal.
#
# Only the lines added by the given range are inspected, so existing test
# fixtures and placeholder strings never need re-baselining. Two shapes are
# flagged:
#   1. an assignment whose right-hand side is a quoted literal of 8+ chars,
#      e.g. `api_key` bound to a `"sk-live-..."` string. An unquoted right-hand
#      side is an expression (`token = normalize(x)`), not a literal, and is
#      deliberately not flagged.
#   2. unquoted provider tokens identified by their prefix: ghp_, github_pat_,
#      sk-, AKIA..., xox[baprs]-.
#
# Examples (`.env.example`, vault examples) and test fixtures are skipped: they
# hold dummy credentials by design, which no regex can tell apart from real
# ones. Secrets pasted into tests are left to review, not to this gate.
#
# Usage: scripts/check_hardcoded_secrets.sh [RANGE]
#   RANGE is anything `git diff` accepts, e.g. origin/dev...HEAD.
#   Without an argument the range is derived from the GitHub Actions env
#   (GITHUB_EVENT_NAME / GITHUB_BASE_REF / GITHUB_EVENT_BEFORE), defaulting to
#   HEAD^...HEAD for local runs.

set -euo pipefail

if [[ $# -gt 0 ]]; then
  range="$1"
else
  case "${GITHUB_EVENT_NAME:-local}" in
    pull_request)
      range="origin/${GITHUB_BASE_REF:?GITHUB_BASE_REF is not set}...HEAD"
      ;;
    push)
      before="${GITHUB_EVENT_BEFORE:-}"
      if [[ -z "$before" || "$before" =~ ^0+$ ]]; then
        range="HEAD^...HEAD"
      else
        range="${before}...HEAD"
      fi
      ;;
    *)
      range="HEAD^...HEAD"
      ;;
  esac
fi

q='["'"'"']'
literal="(password|passwd|api_key|apikey|secret|token|credential)[[:space:]]*[:=][[:space:]]*${q}[^\"']{8,}${q}"
prefixed='(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,})'
excludes=(':!*example' ':!*Example' ':!*.example' ':!*.j2' ':!*.md' ':!*.txt'
          ':!tests/**' ':!*/tests/**' ':!*_test.py' ':!test_*.py')

# Emit "file:line:content" for every added line, skipping examples/docs.
added=$(git diff --unified=0 --no-color --no-ext-diff "$range" -- . "${excludes[@]}" | awk '
  /^\+\+\+ / { file = substr($0, 7); sub(/^b\//, "", file); next }
  /^@@ /     { match($0, /\+[0-9]+/); line = substr($0, RSTART + 1, RLENGTH - 1) + 0; next }
  /^\+/      { printf "%s:%d:%s\n", file, line, substr($0, 2); line++; next }
')

findings=$(printf '%s\n' "$added" | grep -E -e "$literal" -e "$prefixed" || true)

if [[ -n "$findings" ]]; then
  echo "::error::Hardcoded secret literal added by $range"
  printf '%s\n' "$findings"
  exit 1
fi
echo "No hardcoded secret literal added by $range."
