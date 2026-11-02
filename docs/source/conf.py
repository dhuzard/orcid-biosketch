"""Sphinx configuration for the scientist-facing ORCID Playground documentation."""
project = "ORCID Playground"
author = "ORCID Playground contributors"
copyright = "2026, ORCID Playground contributors"
extensions = ["myst_parser"]
root_doc = "index"
source_suffix = {".md": "markdown"}
templates_path = []
exclude_patterns = []
html_theme = "furo"
html_title = "ORCID Playground | Documentation"
html_show_sphinx = False
html_theme_options = {
    "source_repository": "https://github.com/dhuzard/orcid-playground/",
    "source_branch": "main",
    "source_directory": "docs/source/",
}
myst_heading_anchors = 3
