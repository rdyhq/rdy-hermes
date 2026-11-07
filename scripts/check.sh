#!/usr/bin/env bash
# Leak scan for this repo (Check 4).
#
#   scripts/check.sh --words <word list>
#
# The word list is a private file kept OUTSIDE the repo: one word or phrase per
# line (names of people and businesses, private paths, store names). Lines
# starting with # are skipped. Matching ignores case.
#
# It scans every tracked file, every commit message, and every commit's author
# and committer, and fails on:
#   - a word from the list;
#   - an email other than a GitHub noreply address;
#   - a private home path;
#   - something shaped like a key or token;
#   - an author or committer that is not rdy with a GitHub noreply address.
# A self-test first plants one sample of each kind in a throwaway repo and
# fails unless every one is caught.
#
# Exit 0: no hits. Exit 1: hits (listed). Exit 2: bad use or a failed self-test.

set -u

usage() { echo "usage: scripts/check.sh --words <word list outside the repo>" >&2; exit 2; }

words=""
while [ $# -gt 0 ]; do
  case $1 in
    --words) [ $# -ge 2 ] || usage; words=$2; shift 2 ;;
    -h|--help) sed -n '2,20p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) usage ;;
  esac
done
[ -n "$words" ] || usage
[ -f "$words" ] || { echo "word list not found: $words" >&2; exit 2; }

repo=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "run inside the repo" >&2; exit 2; }
words=$(cd "$(dirname "$words")" && pwd)/$(basename "$words")
case $words in
  "$repo"/*) echo "keep the word list outside the repo" >&2; exit 2 ;;
esac

# Patterns are split in two so this file does not match itself.
noreply='@users[.]noreply[.]github[.]com'
email_re='[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+[.][A-Za-z]{2,}'
path_re='(/ho''me/[a-z]|/Use''rs/[A-Za-z]|[A-Za-z]:\\\\Use''rs\\\\|/mn''t/[a-z]/)'
key_re='(s''k-[A-Za-z0-9_-]{20,}|gh''p_[A-Za-z0-9]{30,}|github_p''at_[A-Za-z0-9_]{20,}|AK''IA[0-9A-Z]{16}|xo''x[abprs]-[A-Za-z0-9-]{10,}|glp''at-[A-Za-z0-9_-]{20,}|-----BEG''IN [A-Z ]*PRIVATE KEY-----)'

# scan_text <label> : reads text on stdin, prints "label: kind: line" per hit.
scan_text() {
  label=$1
  awk -v label="$label" -v words="$words" -v email="$email_re" -v noreply="$noreply" \
      -v path="$path_re" -v key="$key_re" '
    BEGIN {
      n = 0
      while ((getline w < words) > 0) {
        sub(/\r$/, "", w); sub(/^[ \t]+/, "", w); sub(/[ \t]+$/, "", w)
        if (w == "" || w ~ /^#/) continue
        list[++n] = tolower(w)
      }
    }
    {
      line = $0; low = tolower(line)
      for (i = 1; i <= n; i++) if (index(low, list[i])) print label ": word: " line
      rest = line
      while (match(rest, email)) {
        found = substr(rest, RSTART, RLENGTH)
        if (found !~ noreply "$") print label ": email: " line
        rest = substr(rest, RSTART + RLENGTH)
      }
      if (line ~ path) print label ": private path: " line
      if (line ~ key) print label ": key or token: " line
    }'
}

# scan_repo <dir> : prints every hit in that repo.
scan_repo() {
  dir=$1
  ( cd "$dir" || exit 2
    git ls-files -z | while IFS= read -r -d '' f; do
      [ -f "$f" ] || continue
      scan_text "$f" < "$f"
    done
    git log --all --format='%H%x09%an%x09%ae%x09%cn%x09%ce' | while IFS=$'\t' read -r h an ae cn ce; do
      short=${h:0:7}
      for pair in "author:$an:$ae" "committer:$cn:$ce"; do
        role=${pair%%:*}; rest=${pair#*:}; name=${rest%%:*}; mail=${rest#*:}
        if [ "$name" != "rdy" ] || ! printf '%s' "$mail" | grep -Eq "^[A-Za-z0-9._+-]+$noreply\$"; then
          echo "commit $short: $role is not rdy with a GitHub noreply address"
        fi
      done
      git log -1 --format='%B' "$h" | scan_text "commit $short message"
    done
  )
}

# Self-test: one planted sample of each kind must be caught.
self_test() {
  tmp=$(mktemp -d) || return 2
  planted_word=$(grep -v '^#' "$words" | grep -v '^[[:space:]]*$' | head -1)
  [ -n "$planted_word" ] || { echo "self-test: the word list is empty" >&2; rm -rf "$tmp"; return 2; }
  (
    cd "$tmp" && git init -q && git config user.name "Sample Person" && git config core.autocrlf false && git config user.email "sample@""example.org"
    {
      echo "notes about $planted_word"
      echo "write to sample@""example.org"
      echo "saved in /ho""me/sample/garden"
      echo "token gh""p_abcdefghijklmnopqrstuvwxyz0123456789"
    } > planted.txt
    git add planted.txt && git commit -q -m "planted sample"
  ) || { rm -rf "$tmp"; return 2; }
  hits=$(scan_repo "$tmp")
  rm -rf "$tmp"
  ok=0
  for kind in "word:" "email:" "private path:" "key or token:" "author is not rdy" "committer is not rdy"; do
    if ! printf '%s\n' "$hits" | grep -q "$kind"; then
      echo "self-test: missed the planted $kind" >&2; ok=2
    fi
  done
  return $ok
}

if ! self_test; then
  echo "leak scan: self-test FAILED, so the scan cannot be trusted" >&2
  exit 2
fi
echo "leak scan: self-test passed (6 planted kinds caught)"

files=$(git -C "$repo" ls-files | wc -l | tr -d ' ')
commits=$(git -C "$repo" rev-list --all | wc -l | tr -d ' ')
hits=$(scan_repo "$repo")
if [ -n "$hits" ]; then
  printf '%s\n' "$hits"
  echo "leak scan: $(printf '%s\n' "$hits" | wc -l | tr -d ' ') hit(s) in $files files and $commits commits"
  exit 1
fi
echo "leak scan: 0 hits in $files files and $commits commits (contents, messages, author and committer)"
exit 0
