#!/usr/bin/env python3
"""Проверка согласованности и покрытия спецификации.

Читает Markdown-разделы из папки (по умолчанию example/) и проверяет:
  * что все упомянутые ID (BG, FR, NFR, UC, AF, методы API, BR, T, AC, коды ошибок)
    определены в своём разделе;
  * что у каждого ФТ, бизнес-правила и НФТ есть хотя бы один критерий приёмки;
  * что каждое ФТ есть в матрице трассируемости (раздел 13.2);
  * что у каждого метода API есть хотя бы одно ФТ (раздел 13.5);
  * что каждый критерий приёмки ссылается хотя бы на одно требование.

Запуск:  python3 tools/check_traceability.py [папка_со_спецификацией]
Код возврата 0 — ошибок нет, 1 — найдены ошибки (удобно для CI).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_DIR = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "example"

ID_RE = re.compile(r"\b(?:FR|NFR|BR|BG|T|AF)-\d+\b|\bAC-N?\d+\b|\bUC\d+(?:\.\d+)?\b|\b[AWE]\d{1,2}\b")
CODE_RE = re.compile(r"`([A-Z]+(?:_[A-Z]+)+)`")


def read(prefix: str) -> str:
    files = sorted(SPEC_DIR.glob(f"{prefix}_*.md"))
    if not files:
        sys.exit(f"Не найден раздел {prefix}_*.md в {SPEC_DIR}")
    return files[0].read_text(encoding="utf-8")


def table_rows(text: str, first_cell: str) -> dict[str, list[str]]:
    """Строки Markdown-таблиц, у которых первая ячейка подходит под шаблон."""
    rows: dict[str, list[str]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and re.fullmatch(first_cell, cells[0]):
            rows[cells[0]] = cells
    return rows


def ids_in(cell: str, kind: str) -> set[str]:
    return set(re.findall(rf"\b{kind}-N?\d+\b", cell))


def main() -> int:
    s01, s03, s04, s041 = read("01"), read("03"), read("04"), read("04.1")
    s05, s08, s10, s12, s13 = read("05"), read("08"), read("10"), read("12"), read("13")
    spec_files = [p for p in sorted(SPEC_DIR.glob("*.md")) if p.name.lower() != "readme.md"]
    all_text = "\n".join(p.read_text(encoding="utf-8") for p in spec_files)

    # --- Что определено --------------------------------------------------
    bg = set(table_rows(s01, r"BG-\d+"))
    fr = set(table_rows(s03, r"FR-\d+"))
    nfr = set(table_rows(s03, r"NFR-\d+"))
    uc = set(table_rows(s04, r"UC\d+(?:\.\d+)?"))
    alt_flows = set(table_rows(s041, r"AF-\d+"))
    br = set(table_rows(s10, r"BR-\d+"))
    transitions = set(table_rows(s08, r"T-\d+"))
    ac_rows = table_rows(s12, r"AC-N?\d+")
    ac = set(ac_rows)
    api = set(table_rows(s05, r"[AWE]\d+"))
    codes = {m.group(1) for m in re.finditer(r"^\| \d{3} \| `([A-Z_]+)`", s05, re.M)}
    defined = bg | fr | nfr | uc | alt_flows | br | transitions | ac | api

    errors: list[str] = []
    warnings: list[str] = []

    # --- 1. Ссылки на несуществующие ID ----------------------------------
    for ref in sorted(set(ID_RE.findall(all_text)) - defined):
        errors.append(f"Ссылка на неопределённый ID: {ref}")

    known_non_errors = {"NOT_NULL"}
    for code in sorted(set(CODE_RE.findall(all_text)) - codes - known_non_errors):
        errors.append(f"Код ошибки не описан в каталоге 5.4: {code}")

    # --- 2. Критерии приёмки и их связи ----------------------------------
    ac_links: dict[str, set[str]] = {}
    for ac_id, cells in ac_rows.items():
        link_cell = cells[1] if len(cells) > 1 else ""
        links = ids_in(link_cell, "FR") | ids_in(link_cell, "BR") | ids_in(link_cell, "NFR")
        if not links:
            errors.append(f"{ac_id} не ссылается ни на одно требование или правило")
        ac_links[ac_id] = links

    def covered_by(item: str) -> set[str]:
        return {a for a, links in ac_links.items() if item in links}

    for group, items in (("ФТ", fr), ("Бизнес-правило", br), ("НФТ", nfr)):
        for item in sorted(items, key=lambda x: int(x.split("-")[1])):
            if not covered_by(item):
                errors.append(f"{group} {item} не покрыто ни одним критерием приёмки")

    # --- 3. Матрица 13.2 -------------------------------------------------
    matrix = table_rows(s13, r"FR-\d+")
    for item in sorted(fr - set(matrix), key=lambda x: int(x[3:])):
        errors.append(f"{item} отсутствует в матрице 13.2")
    for item, cells in matrix.items():
        row_acs = ids_in(cells[-1], "AC")
        row_brs = ids_in(" ".join(cells), "BR")
        if not row_acs:
            errors.append(f"В матрице у {item} нет критериев приёмки")
        for a in sorted(row_acs):
            if a in ac_links and not (ac_links[a] & ({item} | row_brs)):
                warnings.append(f"Матрица: {a} указан для {item}, но не ссылается ни на {item}, ни на его правила")
        for a in sorted(covered_by(item) - row_acs):
            warnings.append(f"{a} ссылается на {item}, но не указан в матрице 13.2")

    # --- 4. API → требования (13.5) --------------------------------------
    api_matrix = table_rows(s13, r"[AWE]\d+")
    for a in sorted(api):
        if a not in api_matrix or not ids_in(" ".join(api_matrix[a]), "FR"):
            errors.append(f"Метод API {a} не связан ни с одним ФТ в 13.5")

    # --- 5. Переходы статусов в матрице ----------------------------------
    matrix_text = "\n".join(" ".join(c) for c in matrix.values())
    for t in sorted(transitions):
        if t not in matrix_text:
            warnings.append(f"Переход {t} не упомянут в матрице 13.2")

    # --- Отчёт ------------------------------------------------------------
    def line(name: str, total: int, missing: int) -> str:
        return f"| {name} | {total} | {total - missing} | {missing} |"

    fr_missing = sum(1 for f in fr if not covered_by(f))
    br_missing = sum(1 for b in br if not covered_by(b))
    nfr_missing = sum(1 for n in nfr if not covered_by(n))
    api_missing = sum(1 for a in api if a not in api_matrix)
    t_missing = sum(1 for t in transitions if t not in matrix_text)

    print(f"Спецификация: {SPEC_DIR}")
    print()
    print("| Что проверяется | Всего | Покрыто | Не покрыто |")
    print("|---|---|---|---|")
    print(line("ФТ с критерием приёмки", len(fr), fr_missing))
    print(line("Бизнес-правила с критерием", len(br), br_missing))
    print(line("НФТ с проверкой", len(nfr), nfr_missing))
    print(line("Методы API с ФТ", len(api), api_missing))
    print(line("Переходы статусов в матрице", len(transitions), t_missing))
    print()
    print(f"Определено: {len(fr)} ФТ, {len(nfr)} НФТ, {len(br)} правил, {len(ac)} критериев, "
          f"{len(api)} методов API, {len(codes)} кодов ошибок, {len(transitions)} переходов")
    print()

    for w in warnings:
        print(f"ПРЕДУПРЕЖДЕНИЕ: {w}")
    for e in errors:
        print(f"ОШИБКА: {e}")

    if errors:
        print(f"\nНайдено ошибок: {len(errors)}")
        return 1
    print("Ошибок не найдено.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
