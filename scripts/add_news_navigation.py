"""Add consistent site navigation to authored newspaper pages in the built site.

Run after build_site.py, so older editions and future articles gain the same
navigation without modifying authored issues or generated directory indexes.
"""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "_site"
NEWS = SITE / "News"


def main() -> None:
    if not NEWS.exists():
        return
    for path in NEWS.rglob("*.html"):
        # The generated archive uses the regular site template and already has a home link.
        if path == NEWS / "index.html":
            continue
        source = path.read_text(encoding="utf-8")
        if 'id="learning-site-nav"' in source:
            continue
        depth = len(path.parent.relative_to(SITE).parts)
        root = "../" * depth
        nav = (
            '<nav id="learning-site-nav" aria-label="Site navigation" '
            'style="padding:.7rem 1rem;margin:0 auto;max-width:1100px;'
            'font:600 14px/1.5 system-ui,sans-serif">'
            f'<a href="{root}" style="margin-right:1.4rem">← Learning home</a>'
            f'<a href="{root}News/">All editions</a>'
            '</nav>'
        )
        revised, count = re.subn(r"(<body\b[^>]*>)", lambda m: m.group(1) + "\n" + nav, source, count=1, flags=re.IGNORECASE)
        if count:
            path.write_text(revised, encoding="utf-8")


if __name__ == "__main__":
    main()
