#!/usr/bin/env bash
# Veröffentlicht den aktuellen Branch auf GitHub Pages, indem er auf den
# Release-Branch `web` geschoben wird. Den Build macht danach die Action
# .github/workflows/pages.yml.
set -euo pipefail

cd "$(dirname "$0")"

RELEASE=web
BRANCH=$(git rev-parse --abbrev-ref HEAD)
REPO=$(git remote get-url origin | sed -E 's#(git@github\.com:|https://github\.com/)([^/]+/[^/.]+)(\.git)?#\2#')

if [ "$BRANCH" = "$RELEASE" ]; then
  echo "Du bist bereits auf '$RELEASE'. Bitte vom Entwicklungs-Branch aus veröffentlichen." >&2
  exit 1
fi

if [ -n "$(git status --porcelain)" ]; then
  echo "Arbeitsverzeichnis ist nicht sauber – bitte erst committen oder stashen." >&2
  git status --short >&2
  exit 1
fi

echo "==> Probelauf, damit nichts Kaputtes auf '$RELEASE' landet"
[ -d web/node_modules ] || npm --prefix web ci
npm --prefix web run check
npm --prefix web run build

echo "==> $BRANCH -> $RELEASE"
git push origin "$BRANCH:$RELEASE"

echo
echo "Workflow: https://github.com/$REPO/actions"
echo "Seite:    https://$(echo "${REPO%%/*}" | tr A-Z a-z).github.io/${REPO##*/}/"
