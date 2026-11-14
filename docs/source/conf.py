"""Sphinx configuration for the scientist-facing documentation.

The product's display name comes from config/brand.json; Markdown pages use it
as ``{{ brand }}``.
"""
import json
from pathlib import Path

BRAND = json.loads((Path(__file__).resolve().parents[2] / "config" / "brand.json").read_text(encoding="utf-8"))
project = BRAND["name"]
author = BRAND["owner"]
copyright = f"2026, {BRAND['owner']} ({BRAND['license']} license). {BRAND['trademark']}"
extensions = ["myst_parser"]
root_doc = "index"
source_suffix = {".md": "markdown"}
templates_path = []
exclude_patterns = []
html_theme = "furo"
html_title = f"{BRAND['name']} | How it works"
html_show_sphinx = False
html_logo = "../../brand/mark.svg"
html_favicon = "../../brand/favicon.svg"
html_theme_options = {
    "source_repository": "https://github.com/dhuzard/science-record-player/",
    "source_branch": "main",
    "source_directory": "docs/source/",
    # The same Science Record Player menu as the app pages (#54); the docs are served at /docs/.
    "announcement": (f"{BRAND['disclaimer']} Developed and maintained independently by {BRAND['owner']} under the {BRAND['license']} license."
                     ' <nav aria-label="Science Record Player"><a href="/">Explore</a> · <a href="/network/">My Network</a> · '
                     '<a href="/group/">Public Group View</a> · <a href="/docs/" aria-current="page">How it works</a> · <a href="/feedback/">Feedback</a></nav>'),
    # Muted pink / aubergine, distinct from ORCID's visual identity.
    "light_css_variables": {"color-brand-primary": "#3a2737", "color-brand-content": "#7a3d55", "color-announcement-background": "#e2b4c0", "color-announcement-text": "#3a2737"},
    "dark_css_variables": {"color-brand-primary": "#e2b4c0", "color-brand-content": "#e2b4c0", "color-announcement-background": "#3a2737", "color-announcement-text": "#f6e6eb"},
}
myst_heading_anchors = 3
myst_enable_extensions = ["substitution"]
myst_substitutions = {key: BRAND[key] for key in ("name", "owner", "license", "disclaimer", "trademark")} | {"brand": BRAND["name"]}
