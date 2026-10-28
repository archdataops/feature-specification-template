#!/usr/bin/env bash
# Включает GitHub Pages (источник — GitHub Actions) и запускает публикацию Swagger UI.
# Запускать после того, как репозиторий стал публичным. Подробности: docs/publishing.md
set -euo pipefail

REPO="archdataops/feature-specification-template"

if gh api "repos/$REPO/pages" --jq '.build_type' >/dev/null 2>&1; then
  echo "Pages уже включён, проверяю источник..."
  gh api -X PUT "repos/$REPO/pages" -f build_type=workflow >/dev/null
else
  echo "Включаю Pages..."
  gh api -X POST "repos/$REPO/pages" -f build_type=workflow >/dev/null
fi

gh workflow run spec-checks.yml -R "$REPO"
echo "Публикация запущена. Следить: gh run watch"
echo "Адрес: https://archdataops.github.io/feature-specification-template/"
