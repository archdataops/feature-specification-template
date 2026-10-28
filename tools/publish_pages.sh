#!/usr/bin/env bash
# Включает GitHub Pages (источник — GitHub Actions), запускает публикацию Swagger UI
# и показывает ход выполнения. Запускать из корня репозитория после того,
# как репозиторий стал публичным. Подробности: docs/publishing.md
set -euo pipefail

REPO="archdataops/feature-specification-template"
WORKFLOW="spec-checks.yml"

if gh api "repos/$REPO/pages" --jq '.build_type' >/dev/null 2>&1; then
  echo "Pages уже включён, устанавливаю источник GitHub Actions..."
  gh api -X PUT "repos/$REPO/pages" -f build_type=workflow >/dev/null
else
  echo "Включаю Pages..."
  gh api -X POST "repos/$REPO/pages" -f build_type=workflow >/dev/null
fi

# Запоминаем последний запуск, чтобы отличить от него новый
before=$(gh run list -R "$REPO" --workflow "$WORKFLOW" -L 1 --json databaseId --jq '.[0].databaseId // 0')

gh workflow run "$WORKFLOW" -R "$REPO"
echo "Публикация запущена, жду появления запуска..."

# GitHub регистрирует запуск через несколько секунд — ждём до 60 секунд
run_id=""
for _ in $(seq 1 30); do
  sleep 2
  latest=$(gh run list -R "$REPO" --workflow "$WORKFLOW" -L 1 --json databaseId --jq '.[0].databaseId // 0')
  if [ "$latest" != "$before" ]; then
    run_id="$latest"
    break
  fi
done

if [ -z "$run_id" ]; then
  echo "Запуск не появился за минуту. Посмотрите вкладку Actions или выполните: gh run watch"
  exit 1
fi

gh run watch "$run_id" -R "$REPO" --exit-status
echo
echo "Готово. Через 1–2 минуты сайт доступен: https://archdataops.github.io/feature-specification-template/"
