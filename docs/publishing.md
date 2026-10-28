# Публикация Swagger UI на GitHub Pages

Swagger UI публикуется workflow [`spec-checks.yml`](../.github/workflows/spec-checks.yml) из ветки `main`.

**Адрес:** https://archdataops.github.io/feature-specification-template/

## Как это работает с приватным репозиторием

- На бесплатном тарифе GitHub Pages работает только для **публичных** репозиториев.
- Пока репозиторий приватный, задание «Публикация Swagger UI» в workflow **пропускается** (серый значок), проверки при этом продолжают работать.
- При переводе репозитория в приват GitHub **снимает сайт с публикации**, а настройка Pages может сброситься.

## Включить снова после того, как репозиторий стал публичным

Одной командой из корня репозитория:

```bash
tools/publish_pages.sh
```

Скрипт включает Pages (или переключает источник на GitHub Actions), запускает workflow, дожидается появления нового запуска и показывает его ход. Завершается с ошибкой, если запуск упал.

**Перед запуском проверьте:**

- [ ] Репозиторий публичный: **Settings → General → Danger Zone → Change visibility**.
- [ ] `gh` авторизован: `gh auth status` показывает `Logged in to github.com account archdataops`.
- [ ] Workflow `.github/workflows/spec-checks.yml` и скрипт `tools/publish_pages.sh` запушены в `main`.
- [ ] Команда запускается из корня репозитория.

> [!WARNING]
> **Скрипт ещё не запускался по-настоящему.** Он проверен только на синтаксис (`bash -n`), потому что при его написании не было доступа к GitHub-аккаунту. Первый боевой запуск будет при следующем распривачивании репозитория.
>
> Если скрипт завершится с ошибкой:
> 1. Сохраните его вывод целиком.
> 2. Выполните шаги вручную по инструкции ниже — они проверены и работают.
> 3. Исправьте скрипт по выводу ошибки и уберите это предупреждение, когда скрипт отработает успешно.

Или вручную:

```bash
# 1. Включить Pages с источником GitHub Actions
#    (если Pages уже включён, GitHub ответит ошибкой «already exists» — это нормально)
gh api -X POST repos/archdataops/feature-specification-template/pages -f build_type=workflow

# 2. Запустить публикацию
gh workflow run spec-checks.yml

# 3. Подождать 5–10 секунд, пока GitHub зарегистрирует запуск, и следить за ним
#    (выбрать верхний, самый свежий запуск)
gh run watch
```

Через 1–2 минуты после зелёного запуска сайт доступен по адресу выше.

То же через браузер:
1. **Settings → Pages → Build and deployment → Source:** выбрать **GitHub Actions**.
2. **Actions → Spec checks → Run workflow**.

## Проверить текущее состояние

```bash
gh api repos/archdataops/feature-specification-template/pages --jq '.html_url, .build_type'
```

| Ответ | Что значит |
|-------|------------|
| Адрес сайта и `workflow` | Pages включён, источник — GitHub Actions |
| `Not Found` | Pages выключен — выполнить шаг 1 |
| Адрес сайта и `legacy` | Источник — ветка, а не Actions. Выполнить: `gh api -X PUT repos/archdataops/feature-specification-template/pages -f build_type=workflow` |

## Если что-то пошло не так

| Симптом | Причина | Что делать |
|---------|---------|------------|
| Задание «Публикация Swagger UI» серое (пропущено) | Workflow запущен, пока репозиторий был приватным | Запустить workflow ещё раз |
| Задание упало на шаге `deploy-pages` | Pages не включён или источник не GitHub Actions | Шаг 1, затем перезапуск |
| Упали «Проверки спецификации» | Расхождение в спецификации, OpenAPI или диаграммах | `gh run view --log-failed` и исправить по сообщению ([tools/README.md](../tools/README.md)) |
| Сайт открывается пустым или 404 | Публикация ещё не разошлась | Подождать 1–2 минуты, обновить без кэша (`Ctrl+Shift+R`) |
| `gh: To get started with GitHub CLI, please run: gh auth login` | `gh` не авторизован | `gh auth login` → GitHub.com → HTTPS → Login with a web browser |

## Посмотреть Swagger UI без публикации

Из корня репозитория:

```bash
python3 -m http.server 8000
```

и открыть http://localhost:8000/docs/
