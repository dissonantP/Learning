from __future__ import annotations

import html
import re
import shutil
from pathlib import Path
from urllib.parse import quote

import markdown

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"
SKIP_PARTS = {".git", "_site", "__pycache__"}
TEXT_SUFFIXES = {
    ".md", ".html", ".htm", ".txt", ".py", ".rb", ".js", ".ts", ".tsx",
    ".jsx", ".json", ".yml", ".yaml", ".toml", ".css", ".scss", ".sh",
    ".fish", ".cs", ".xml", ".ini", ".cfg", ".conf",
}


def skipped(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    return any(part in SKIP_PARTS for part in rel.parts)


def rel_root(output_path: Path) -> str:
    depth = len(output_path.parent.relative_to(OUT).parts)
    return "../" * depth


def page(title: str, body: str, output_path: Path) -> str:
    root = rel_root(output_path)
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
  <title>{html.escape(title)} · Learning</title>
  <link rel=\"stylesheet\" href=\"{root}assets/site.css\">
</head>
<body>
  <header class=\"site-header\">
    <a class=\"brand\" href=\"{root}\">Learning</a>
    <nav>
      <a href=\"{root}News/\">Newspaper</a>
      <a href=\"{root}Learning/Focuses.html\">Focuses</a>
      <a href=\"https://github.com/dissonantP/Learning\">GitHub</a>
    </nav>
  </header>
  <main class=\"content\">{body}</main>
</body>
</html>
"""


def markdown_title(source: str, fallback: str) -> str:
    match = re.search(r"^#\s+(.+)$", source, flags=re.MULTILINE)
    return match.group(1).strip() if match else fallback


def rewrite_markdown_links(rendered: str) -> str:
    return re.sub(r'href="([^"#?]+)\.md([#?][^"]*)?"', lambda m: f'href="{m.group(1)}.html{m.group(2) or ""}"', rendered)


def render_markdown(src: Path, dest: Path) -> None:
    text = src.read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["extra", "sane_lists", "toc"])
    body = rewrite_markdown_links(body)
    title = markdown_title(text, src.stem)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(page(title, f'<article class="markdown-body">{body}</article>', dest), encoding="utf-8")


def source_view(src: Path, rel: Path) -> None:
    try:
        text = src.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return
    dest = OUT / "_source" / Path(str(rel) + ".html")
    dest.parent.mkdir(parents=True, exist_ok=True)
    body = f"<h1>{html.escape(rel.as_posix())}</h1><pre class=\"source\"><code>{html.escape(text)}</code></pre>"
    dest.write_text(page(rel.as_posix(), body, dest), encoding="utf-8")


def built_target(rel: Path) -> str:
    if rel.suffix.lower() == ".md":
        return rel.with_suffix(".html").as_posix()
    if rel.suffix.lower() in {".html", ".htm"}:
        return rel.as_posix()
    if rel.suffix.lower() in TEXT_SUFFIXES:
        return (Path("_source") / Path(str(rel) + ".html")).as_posix()
    return rel.as_posix()


def breadcrumbs(rel_dir: Path) -> str:
    if rel_dir == Path("."):
        return ""
    parts = rel_dir.parts
    links = ['<a href="' + ("../" * len(parts)) + '">Learning</a>']
    for i, part in enumerate(parts):
        href = "../" * (len(parts) - i - 1)
        links.append(f'<a href="{href or "./"}">{html.escape(part)}</a>')
    return '<div class="breadcrumbs">' + " / ".join(links) + "</div>"


def directory_listing(src_dir: Path) -> str:
    rel_dir = src_dir.relative_to(ROOT)
    if rel_dir == Path("."):
        title = "Learning"
    elif rel_dir == Path("News"):
        title = "Learning Newspaper"
    else:
        title = rel_dir.as_posix()

    entries = []
    children = [p for p in src_dir.iterdir() if not skipped(p)]
    children.sort(key=lambda p: (not p.is_dir(), p.name.lower()))

    for child in children:
        rel = child.relative_to(ROOT)
        name = child.name
        if child.is_dir():
            href = quote(name) + "/"
            kind = "Directory"
        else:
            if rel_dir == Path(".") and name == "index.html":
                href = "_source/index.html.html"
            elif child.suffix.lower() == ".md":
                href = quote(child.with_suffix(".html").name)
            elif child.suffix.lower() in {".html", ".htm"}:
                href = quote(name)
            elif child.suffix.lower() in TEXT_SUFFIXES:
                depth = len(rel_dir.parts) if rel_dir != Path(".") else 0
                href = ("../" * depth) + quote((Path("_source") / Path(str(rel) + ".html")).as_posix(), safe="/")
            else:
                href = quote(name)
            kind = child.suffix.lstrip(".").upper() or "File"
        entries.append(f'<li><a href="{href}">{html.escape(name)}</a><span>{kind}</span></li>')

    extra = ""
    readme = src_dir / "README.md"
    if readme.exists():
        readme_html = markdown.markdown(readme.read_text(encoding="utf-8"), extensions=["extra", "sane_lists"])
        readme_html = rewrite_markdown_links(readme_html)
        extra = f'<section class="readme"><h2>README</h2>{readme_html}</section>'

    if rel_dir == Path("."):
        editions = sorted((ROOT / "News").glob("20??-??-??*"), key=lambda p: p.name, reverse=True) if (ROOT / "News").exists() else []
        latest = editions[0].name if editions else None
        hero = (
            f'<section class="hero"><div><p class="eyebrow">Latest edition</p><h1>Learning</h1><p>A browsable knowledge base and daily learning newspaper.</p></div>'
            + (f'<a class="button" href="News/{quote(latest)}/">Read {html.escape(latest)}</a>' if latest else '<a class="button" href="News/">Newspaper</a>')
            + '</section>'
        )
    elif rel_dir == Path("News"):
        editions = sorted([p for p in src_dir.iterdir() if p.is_dir() and re.match(r"^\d{4}-\d{2}-\d{2}", p.name)], key=lambda p: p.name, reverse=True)
        latest = editions[0].name if editions else None
        hero = '<section class="hero"><div><p class="eyebrow">Archive</p><h1>Learning Newspaper</h1><p>Dated learning reports across the current focuses.</p></div>'
        if latest:
            hero += f'<a class="button" href="{quote(latest)}/">Latest: {html.escape(latest)}</a>'
        hero += '</section>'
    else:
        hero = f'<h1>{html.escape(title)}</h1>'

    return breadcrumbs(rel_dir) + hero + '<section><h2>Browse</h2><ul class="file-list">' + "".join(entries) + "</ul></section>" + extra


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    for src in ROOT.rglob("*"):
        if skipped(src) or src.is_dir():
            continue
        rel = src.relative_to(ROOT)

        if rel == Path("index.html"):
            source_view(src, rel)
            continue

        if src.suffix.lower() == ".md":
            render_markdown(src, OUT / rel.with_suffix(".html"))
            source_view(src, rel)
        elif src.suffix.lower() in {".html", ".htm"}:
            dest = OUT / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            source_view(src, rel)
        else:
            dest = OUT / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            if src.suffix.lower() in TEXT_SUFFIXES:
                source_view(src, rel)

    for src_dir in [ROOT] + [p for p in ROOT.rglob("*") if p.is_dir() and not skipped(p)]:
        rel_dir = src_dir.relative_to(ROOT)
        dest_dir = OUT if rel_dir == Path(".") else OUT / rel_dir
        dest_dir.mkdir(parents=True, exist_ok=True)

        authored_index = src_dir / "index.html"
        if rel_dir != Path(".") and authored_index.exists():
            continue

        dest = dest_dir / "index.html"
        title = "Learning" if rel_dir == Path(".") else rel_dir.as_posix()
        dest.write_text(page(title, directory_listing(src_dir), dest), encoding="utf-8")

    (OUT / ".nojekyll").write_text("", encoding="utf-8")


if __name__ == "__main__":
    main()
