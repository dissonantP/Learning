# Repository conventions

This repository is a browsable learning knowledge base with a generated GitHub Pages site.

## Content

- Markdown is the default format for ordinary notes and knowledge-base content.
- Topic-oriented material may live in folders with `README.md` entry points so GitHub's repository UI remains pleasant to browse.
- `Learning/Focuses.md` is the canonical state for scheduled learning focuses.
- Newspaper editions are date-first and live under `News/YYYY-MM-DD/index.html` (or a timestamped variant when necessary).
- Newspaper editions may use authored HTML directly, especially when custom visual presentation or embedded images are useful.

## GitHub Pages

- `scripts/build_site.py` builds the public site into `_site/`.
- The Pages build converts Markdown files to HTML, preserves authored HTML/assets, and generates directory indexes so the repository can be browsed as a website.
- The generated root page is a general repository/knowledge-base index and links to the newspaper; it is not itself the newspaper.
- Do not manually maintain generated directory indexes. Add or edit source content and let the Pages workflow rebuild them.
- `.github/workflows/pages.yml` builds and deploys the site on pushes to `main`.
