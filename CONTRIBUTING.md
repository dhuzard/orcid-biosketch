# Contributing

Contributions from researchers, data stewards, librarians and developers are welcome. **You do not need to code to improve the project.**

## Start with a real task

Open the [hosted playground](https://science-record-player.web.app/) and follow the [five-minute scientist test](docs/source/feedback.md). Using the tool requires no GitHub account; opening an issue does.

Choose [scientist feedback / feature idea](https://github.com/dhuzard/science-record-player/issues/new/choose) and describe:
- The concrete scientific task and intended audience.
- What you tried (sample data or a public record), and what you expected.
- What was missing, confusing or potentially misleading.
- A measurable outcome that would make a change valuable.

**Scientific correction reports, provenance problems and misleading relationship claims take priority** over purely decorative changes.

## For developers

1. Review [AGENTS.md](AGENTS.md), [README.md](README.md), [BACKLOG.md](BACKLOG.md), the relevant schemas and tests.
2. Open an issue to discuss changes that alter privacy, identifiers, ORCID access, data models or exported contracts.
3. Use deterministic synthetic/stored ORCID fixtures for tests; do not put private records or tokens in pull requests.
4. Run `python -m pip install -e ".[dev]"` and `python -m pytest -q`.
5. For documentation changes, also run `python -m pip install -r docs/requirements.txt` and `python -m sphinx -b html -n -W --keep-going docs/source docs/_build/html`.
6. Open a focused PR linked to an issue, explaining compatibility and provenance implications.

A new feature should not imply verification of identity, authorship, collaboration, project membership, CRediT roles or scientific quality that the source does not establish.

## Safety and privacy

Do not publish tokens, contact notes, unpublished personal data, or private research information in screenshots, issues, or test fixtures. For real researcher feedback, use public records or clearly labelled synthetic examples.

This is an independent open-source project and is not affiliated with, sponsored by, or endorsed by ORCID. Do not reintroduce ORCID as the leading product name or ORCID-like colours; the display identity lives in `config/brand.json`.
