# Sphinx documentation

This directory contains existing engineering notes (the Markdown files at its root) and a new **scientist-facing Sphinx guide** under `source/`. Both serve different purposes: end-user tasks versus implementation details.

## Build locally

```bash
python -m pip install -r docs/requirements.txt
python -m sphinx -b html -n -W --keep-going docs/source docs/_build/html
```

Open `docs/_build/html/index.html` in a browser. The documentation CI workflow builds the guide on pull requests, uploads the HTML artifact, and the existing Firebase Hosting workflow also builds and publishes it under **`/docs/`** with the main application.

Public target: <https://science-record-player.web.app/docs/>. Verify the production deployment before announcing that URL publicly.

## Source conventions

- Put short, action-oriented scientist help pages in `source/`.
- Keep protocol-specific, implementation and deployment specifications in root `docs/*.md`.
- Explicitly distinguish **available in the public hosted build**, **implemented but not deployed**, and **proposed**.
- Never imply a public ORCID assertion is a verified identity or project membership.
- Avoid exposing private contact notes or actual participant data in screenshots.
