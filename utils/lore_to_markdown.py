"""One-shot tool: convert per-article HTML lore files to clean Markdown.

Pass 2 of the lore pipeline. Reads every ``docs/lore/<category>/<slug>.html``
file produced by ``utils/split_loredump.py``, strips the World Anvil
scaffolding, converts the article body to Markdown, rewrites internal
``article-link`` anchors as relative ``.md`` links, and writes
``<slug>.md`` next to the source. The ``.html`` source is deleted on
success. ``docs/lore/INDEX.md`` is rewritten to point at the new
``.md`` files.

Run from the repo root:

    python utils/lore_to_markdown.py

Idempotent: a file with no ``.html`` source is silently skipped.
"""

from __future__ import annotations

import html
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LORE_DIR = os.path.join(ROOT, "docs", "lore")
INDEX_PATH = os.path.join(LORE_DIR, "INDEX.md")

# Wrapping div carries the article's UUID and template type.
TEMPLATE_RE = re.compile(
    r"template-(\w+)\s+article-([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
    r"[0-9a-f]{4}-[0-9a-f]{12})"
)
# Header comment written by split_loredump.py: "<!-- Type: Title -->"
HEADER_RE = re.compile(r"<!--\s*([A-Za-z]+):\s*(.+?)\s*-->")


# ---------------------------------------------------------------------------
# HTML SLICING
# ---------------------------------------------------------------------------

def extract_div(text: str, class_name: str) -> str | None:
    """Return the inner HTML of the first ``<div class="class_name ...">``
    block, balancing nested ``<div>`` tags.
    """
    open_re = re.compile(
        r'<div\b[^>]*\bclass="[^"]*\b' + re.escape(class_name) + r'\b[^"]*"[^>]*>'
    )
    m = open_re.search(text)
    if not m:
        return None
    start = m.end()
    depth = 1
    i = start
    div_open = re.compile(r"<div\b[^>]*>", re.IGNORECASE)
    div_close = re.compile(r"</div\s*>", re.IGNORECASE)
    while i < len(text) and depth > 0:
        next_open = div_open.search(text, i)
        next_close = div_close.search(text, i)
        if next_close is None:
            return None
        if next_open and next_open.start() < next_close.start():
            depth += 1
            i = next_open.end()
        else:
            depth -= 1
            if depth == 0:
                return text[start:next_close.start()]
            i = next_close.end()
    return None


def extract_section_pairs(text: str) -> list[tuple[str, str]]:
    """Find every ``section-title`` / ``section-payload`` pair in document order.

    Returns a list of ``(title_html, payload_html)`` tuples. Empty
    payloads are skipped.
    """
    pairs: list[tuple[str, str]] = []
    title_iter = list(re.finditer(
        r'<div\b[^>]*\bclass="[^"]*\bsection-title\b[^"]*"[^>]*>',
        text,
    ))
    payload_iter = list(re.finditer(
        r'<div\b[^>]*\bclass="[^"]*\bsection-payload\b[^"]*"[^>]*>',
        text,
    ))
    if not payload_iter:
        return pairs
    # Pair each payload with the nearest preceding title.
    for p in payload_iter:
        # Find nearest preceding section-title.
        title_html = ""
        for t in title_iter:
            if t.end() <= p.start():
                title_inner = extract_div(text[t.start():], "section-title")
                if title_inner is not None:
                    title_html = title_inner
        payload_inner = extract_div(text[p.start():], "section-payload")
        if payload_inner is None:
            continue
        if not strip_tags(payload_inner).strip():
            continue
        pairs.append((title_html, payload_inner))
    return pairs


# ---------------------------------------------------------------------------
# UUID INDEX
# ---------------------------------------------------------------------------

def build_uuid_index() -> dict[str, tuple[str, str, str]]:
    """Walk all ``.html`` lore files and map article UUID -> (category, slug, title).

    The category is the directory the file lives in; slug is the filename
    without extension; title is the value parsed from the ``<!-- Type: Title -->``
    header comment.
    """
    index: dict[str, tuple[str, str, str]] = {}
    for category in os.listdir(LORE_DIR):
        cat_dir = os.path.join(LORE_DIR, category)
        if not os.path.isdir(cat_dir):
            continue
        for name in os.listdir(cat_dir):
            if not name.endswith(".html"):
                continue
            slug = name[:-5]
            path = os.path.join(cat_dir, name)
            with open(path, "r", encoding="utf-8") as f:
                src = f.read()
            tm = TEMPLATE_RE.search(src)
            hm = HEADER_RE.search(src)
            title = hm.group(2).strip() if hm else slug
            if tm:
                uuid = tm.group(2)
                index[uuid] = (category, slug, title)
    return index


# ---------------------------------------------------------------------------
# HTML -> MARKDOWN
# ---------------------------------------------------------------------------

ARTICLE_LINK_RE = re.compile(
    r'<a\b[^>]*\bdata-article-id="([0-9a-f-]{36})"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
PLAIN_LINK_RE = re.compile(r"<a\b[^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")
WS_RUNS_RE = re.compile(r"[ \t]+")
BLANK_RUNS_RE = re.compile(r"\n{3,}")


def rewrite_article_links(
    body: str,
    src_category: str,
    uuid_index: dict[str, tuple[str, str, str]],
) -> str:
    """Replace ``<a data-article-id="UUID">text</a>`` with Markdown links
    pointing at the converted article. Unknown UUIDs become plain text.
    """

    def repl(m: re.Match[str]) -> str:
        uuid = m.group(1)
        text = strip_tags(m.group(2)).strip()
        if uuid in uuid_index:
            cat, slug, _ = uuid_index[uuid]
            rel = f"../{cat}/{slug}.md"
            return f"[{text}]({rel})"
        return text

    return ARTICLE_LINK_RE.sub(repl, body)


def strip_tags(s: str) -> str:
    """Remove all HTML tags from ``s`` (used for payload-emptiness checks
    and inside link bodies).
    """
    return TAG_RE.sub("", s)


def html_to_markdown(
    body: str,
    src_category: str,
    uuid_index: dict[str, tuple[str, str, str]],
) -> str:
    """Convert a chunk of World-Anvil-flavored HTML into clean Markdown."""
    s = body
    # Article-link anchors first (they carry their own data attributes).
    s = rewrite_article_links(s, src_category, uuid_index)
    # Drop any other anchors (external WA category links etc.) but keep text.
    s = PLAIN_LINK_RE.sub(lambda m: strip_tags(m.group(1)), s)

    # Inline emphasis.
    s = re.sub(r"</?(b|strong)\b[^>]*>", "**", s, flags=re.IGNORECASE)
    s = re.sub(r"</?(i|em)\b[^>]*>", "*", s, flags=re.IGNORECASE)

    # Headings inside payloads.
    for level in range(6, 0, -1):
        s = re.sub(
            rf"<h{level}\b[^>]*>(.*?)</h{level}>",
            lambda m, lv=level: "\n\n" + ("#" * lv) + " " + m.group(1).strip() + "\n\n",
            s,
            flags=re.IGNORECASE | re.DOTALL,
        )

    # Lists.
    s = re.sub(r"<li\b[^>]*>", "\n- ", s, flags=re.IGNORECASE)
    s = re.sub(r"</li\s*>", "", s, flags=re.IGNORECASE)
    s = re.sub(r"</?(ul|ol)\b[^>]*>", "\n", s, flags=re.IGNORECASE)

    # Line breaks and paragraphs.
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<p\b[^>]*>", "\n\n", s, flags=re.IGNORECASE)
    s = re.sub(r"</p\s*>", "\n\n", s, flags=re.IGNORECASE)

    # Drop any remaining tags (spans with inline color, divs, etc.).
    s = TAG_RE.sub("", s)

    # Decode entities (&#039; &amp; &nbsp;) and normalize whitespace.
    s = html.unescape(s)
    s = s.replace("\u00a0", " ")
    # Trim trailing spaces on lines, collapse runs of spaces, collapse blank
    # runs, and drop leading/trailing blank lines.
    lines = [WS_RUNS_RE.sub(" ", ln).rstrip() for ln in s.splitlines()]
    s = "\n".join(lines)
    s = BLANK_RUNS_RE.sub("\n\n", s).strip()
    return s


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def convert_one(
    path: str,
    category: str,
    uuid_index: dict[str, tuple[str, str, str]],
) -> tuple[str, str] | None:
    """Convert a single article file. Returns (title, slug) or None on skip."""
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()

    hm = HEADER_RE.search(src)
    if not hm:
        print(f"WARN: no header in {path}", file=sys.stderr)
        return None
    title = hm.group(2).strip()
    slug = os.path.splitext(os.path.basename(path))[0]

    body_html = extract_div(src, "user-css-vignette") or ""
    body_md = html_to_markdown(body_html, category, uuid_index)

    extra_blocks: list[str] = []
    for title_html, payload_html in extract_section_pairs(src):
        section_title = strip_tags(title_html).strip()
        section_md = html_to_markdown(payload_html, category, uuid_index)
        if not section_md:
            continue
        # Single-line payloads render as a key/value blockquote; multi-line
        # payloads render as a regular subsection. A missing/empty title
        # (some World Anvil templates expose a payload with no label)
        # falls back to a plain blockquote.
        if "\n" in section_md:
            heading = section_title or "Notes"
            extra_blocks.append(f"## {heading}\n\n{section_md}")
        elif section_title:
            extra_blocks.append(f"> **{section_title}:** {section_md}")
        else:
            extra_blocks.append(f"> {section_md}")

    out_lines = [f"# {title}", ""]
    if body_md:
        out_lines.append(body_md)
    if extra_blocks:
        if body_md:
            out_lines.append("")
        out_lines.append("\n\n".join(extra_blocks))
    out_text = "\n".join(out_lines).rstrip() + "\n"

    out_path = os.path.join(os.path.dirname(path), f"{slug}.md")
    with open(out_path, "w", encoding="utf-8") as out:
        out.write(out_text)
    os.remove(path)
    return title, slug


def write_index(by_category: dict[str, list[tuple[str, str]]]) -> None:
    """Rewrite docs/lore/INDEX.md to point at the new ``.md`` files."""
    lines: list[str] = []
    lines.append("# Nuitai Lore Index\n")
    lines.append(
        "Auto-generated by `utils/lore_to_markdown.py` from the per-article "
        "files. To regenerate from scratch, re-run `utils/split_loredump.py` "
        "then `utils/lore_to_markdown.py`. Do not hand-edit this file.\n"
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


def main() -> int:
    if not os.path.isdir(LORE_DIR):
        print(f"ERROR: lore dir not found: {LORE_DIR}", file=sys.stderr)
        return 1

    uuid_index = build_uuid_index()
    by_category: dict[str, list[tuple[str, str]]] = defaultdict(list)
    converted = 0

    for category in sorted(os.listdir(LORE_DIR)):
        cat_dir = os.path.join(LORE_DIR, category)
        if not os.path.isdir(cat_dir):
            continue
        for name in sorted(os.listdir(cat_dir)):
            path = os.path.join(cat_dir, name)
            if name.endswith(".html"):
                result = convert_one(path, category, uuid_index)
                if result is None:
                    continue
                title, slug = result
                converted += 1
            elif name.endswith(".md"):
                slug = name[:-3]
                # Pull the H1 from the existing markdown for the index entry.
                with open(path, "r", encoding="utf-8") as f:
                    first = f.readline().strip()
                title = first.lstrip("# ").strip() or slug
            else:
                continue
            rel = f"{category}/{slug}.md"
            by_category[category].append((title, rel))

    write_index(by_category)
    print(f"Converted {converted} articles. Index: {INDEX_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
