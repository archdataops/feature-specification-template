#!/usr/bin/env python3
"""Синхронизация диаграмм-заготовок шаблона.

Шаблон содержит образцы кода PlantUML прямо в Markdown (блоки ```plantuml).
Скрипт:
  1. извлекает каждый блок в diagrams/template/<имя>.puml;
  2. вставляет над блоком картинку ../diagrams/template/<имя>.svg, если её ещё нет.

После запуска нужно отрендерить SVG:
    java -jar plantuml.jar -tsvg -charset UTF-8 diagrams/template/*.puml

Режим проверки (для CI) ничего не меняет и завершается с кодом 1,
если .puml не совпадают с кодом в шаблоне или не хватает картинок:
    python3 tools/template_diagrams.py --check
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = ROOT / "template"
OUT_DIR = ROOT / "diagrams" / "template"

BLOCK_RE = re.compile(r"```plantuml\n(.*?)```", re.S)
IMAGE_CAPTION = "Как выглядит заготовка"


def diagram_name(md: Path, index: int) -> str:
    """template/01_x.md → 01_x; template/c4/01_y.md → c4_01_y; второй блок в файле → _2."""
    rel = md.relative_to(TEMPLATE_DIR).with_suffix("")
    base = "_".join(rel.parts)
    return base if index == 1 else f"{base}_{index}"


def image_line(md: Path, name: str) -> str:
    svg = OUT_DIR / f"{name}.svg"
    rel = Path(os.path.relpath(svg, md.parent)).as_posix()
    return f"![{IMAGE_CAPTION}]({rel})"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="только проверить, ничего не менять")
    args = parser.parse_args()

    problems: list[str] = []
    expected: set[str] = set()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for md in sorted(TEMPLATE_DIR.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        blocks = list(BLOCK_RE.finditer(text))
        if not blocks:
            continue

        new_text = text
        # Идём с конца, чтобы вставки не сдвигали позиции следующих блоков
        for index, match in reversed(list(enumerate(blocks, start=1))):
            name = diagram_name(md, index)
            expected.add(name)
            code = match.group(1)
            puml = OUT_DIR / f"{name}.puml"

            if not puml.exists() or puml.read_text(encoding="utf-8") != code:
                if args.check:
                    problems.append(f"{puml.relative_to(ROOT)} не совпадает с кодом в {md.relative_to(ROOT)}")
                else:
                    puml.write_text(code, encoding="utf-8")
                    print(f"обновлён {puml.relative_to(ROOT)}")

            img = image_line(md, name)
            before = new_text[: match.start()].rstrip("\n")
            if not before.endswith(img):
                if args.check:
                    problems.append(f"в {md.relative_to(ROOT)} нет картинки над блоком {index}")
                else:
                    new_text = new_text[: match.start()] + img + "\n\n" + new_text[match.start():]

        if new_text != text:
            md.write_text(new_text, encoding="utf-8")
            print(f"добавлены картинки в {md.relative_to(ROOT)}")

    for orphan in sorted(p.stem for p in OUT_DIR.glob("*.puml")):
        if orphan not in expected:
            problems.append(f"diagrams/template/{orphan}.puml больше не используется в шаблоне")

    if args.check:
        for svg_needed in sorted(expected):
            if not (OUT_DIR / f"{svg_needed}.svg").exists():
                problems.append(f"нет отрендеренной картинки diagrams/template/{svg_needed}.svg")

    for p in problems:
        print(f"ОШИБКА: {p}")
    if problems:
        print("\nИсправить: python3 tools/template_diagrams.py и перерисовать SVG")
        return 1
    print(f"Заготовок диаграмм: {len(expected)}, всё синхронизировано.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
