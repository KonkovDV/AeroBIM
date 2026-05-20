#!/usr/bin/env bash
# Rewrite legacy KonkovaElena / test@example.com commits to KonkovDV.
set -euo pipefail

export FILTER_BRANCH_SQUELCH_WARNING=1

git filter-branch -f --env-filter '
if [ "$GIT_AUTHOR_EMAIL" = "test@example.com" ] || [ "$GIT_AUTHOR_NAME" = "KonkovaElena" ]; then
  export GIT_AUTHOR_NAME="KonkovDV"
  export GIT_AUTHOR_EMAIL="KonkovDV@users.noreply.github.com"
fi
if [ "$GIT_COMMITTER_EMAIL" = "test@example.com" ] || [ "$GIT_COMMITTER_NAME" = "KonkovaElena" ]; then
  export GIT_COMMITTER_NAME="KonkovDV"
  export GIT_COMMITTER_EMAIL="KonkovDV@users.noreply.github.com"
fi
' --tag-name-filter cat -- main
