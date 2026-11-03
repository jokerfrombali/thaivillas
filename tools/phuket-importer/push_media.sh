#!/usr/bin/env bash
# Commit and push one media repo in chunks (~150 MB per push) so no single push is too big.
#   push_media.sh /home/user/thaivillas-media-01
# The folder must already contain the files from shard_media.py.
set -euo pipefail
R="$1"; NAME="$(basename "$R")"
cd "$R"
[ -d .git ] || git init -q -b main
git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/jokerfrombali/$NAME"
git fetch -q origin main 2>/dev/null && git reset -q --soft origin/main 2>/dev/null || true
git checkout -q -B main 2>/dev/null || true
push() { for i in 1 2 3 4; do git push -q -u origin main && return 0; sleep $((2**i)); done; return 1; }
git add .nojekyll README.md index.html 2>/dev/null || true
git diff --cached --quiet || { git commit -q -m "Media storage: README and Pages files"; push; }
batch=(); size=0
flush() {
  [ ${#batch[@]} -eq 0 ] && return
  git add -- "${batch[@]}"
  git commit -q -m "Add photos: ${#batch[@]} listings"
  push
  echo "pushed ${#batch[@]} listings ($((size/1048576)) MB)"
  batch=(); size=0
}
for d in */*/; do
  d="${d%/}"
  [ -n "$(git status --porcelain -- "$d")" ] || continue
  s=$(du -sb "$d" | cut -f1)
  batch+=("$d"); size=$((size+s))
  [ $size -ge 157286400 ] && flush
done
flush
echo "done $NAME"
