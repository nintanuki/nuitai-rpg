"""One-shot tool: split docs/LOREDUMP.html into per-article files.

Reads the World Anvil HTML export, slices it on the
``<!-- Type-Name-hash.html -->`` comment markers it embeds between
articles, and writes one ``.html`` file per article into
``docs/lore/<category>/<slug>.html``. Also emits ``docs/lore/INDEX.md``
with a grouped table of contents.

Run from the repo root:

    python utils/split_loredump.py

Idempotent. Safe to re-run after editing LOREDUMP.html.
"""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "docs", "LOREDUMP.html")
OUT_DIR = os.path.join(ROOT, "docs", "lore")
INDEX_PATH = os.path.join(OUT_DIR, "INDEX.md")

# Matches: <!-- Category-Title-hash.html -->
HEADER_RE = re.compile(r"<!--\s*([A-Za-z]+)-(.+?)-([0-9a-f]+)\.html\s*-->")


def slugify(name: str) -> str:
    """Filesystem-safe slug. Keeps unicode letters, swaps spaces for dashes."""
    name = name.strip().replace("’", "'").replace("'", "")
    name = re.sub(r"[\\/:*?\"<>|]+", "", name)
    name = re.sub(r"\s+", "-", name)
    return name.lower()


def main() -> int:
    if not os.path.isfile(SOURCE):
        print(f"ERROR: source not found: {SOURCE}", file=sys.stderr)
        return 1

    with open(SOURCE, "r", encoding="utf-8") as f:
        text = f.read()

    matches = list(HEADER_RE.finditer(text))
    if not matches:
        print("ERROR: no article headers found.", file=sys.stderr)
        return 1

    os.makedirs(OUT_DIR, exist_ok=True)
    # Wipe any prior per-article files so re-runs don't accumulate stale
    # output (e.g. .md files from a previous lore_to_markdown.py run, or
    # .html files for articles that have since been removed from the dump).
    for entry in os.listdir(OUT_DIR):
        sub = os.path.join(OUT_DIR, entry)
        if not os.path.isdir(sub):
            continue
        for name in os.listdir(sub):
            if name.endswith((".html", ".md")):
                os.remove(os.path.join(sub, name))
    by_category: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for i, m in enumerate(matches):
        category = m.group(1)
        title = m.group(2).strip()
        body_start = m.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()

        cat_dir = os.path.join(OUT_DIR, category.lower())
        os.makedirs(cat_dir, exist_ok=True)
        slug = slugify(title)
        out_path = os.path.join(cat_dir, f"{slug}.html")

        with open(out_path, "w", encoding="utf-8") as out:
            out.write(f"<!-- {category}: {title} -->\n")
            out.write(body)
            out.write("\n")

        rel = os.path.relpath(out_path, OUT_DIR).replace(os.sep, "/")
        by_category[category].append((title, rel))

    # Write INDEX.md
    lines: list[str] = []
    lines.append("# Nuitai Lore Index\n")
    lines.append(
        "Auto-generated from `docs/LOREDUMP.html` by "
        "`utils/split_loredump.py`. Do not hand-edit this file; "
        "edit the source and re-run the splitter.\n"
    )
    total = sum(len(v) for v in by_category.values())
    lines.append(f"**{total} articles** across {len(by_category)} categories.\n")

    for category in sorted(by_category):
        entries = sorted(by_category[category], key=lambda e: e[0].lower())
        lines.append(f"\n## {category} ({len(entries)})\n")
        for title, rel in entries:
            lines.append(f"- [{title}]({rel})")

    with open(INDEX_PATH, "w", encoding="utf-8") as out:
        out.write("\n".join(lines) + "\n")

    print(f"Wrote {total} articles into {OUT_DIR}")
    print(f"Wrote index: {INDEX_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
