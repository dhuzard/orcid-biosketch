# Developers and reproducible integration

The hosted browser app is the easiest demonstration, while the **`science_record_player` Python package** supports local, deterministic regeneration and website integration.

## Install and generate

Python 3.10+ from a cloned repository:

```bash
python -m pip install -e .
srp generate 0000-0003-4820-7951 \
  --config config/biosketch.json \
  --output generated
```

The generated directory contains normalized `biosketch.json`, Schema.org `biosketch.jsonld` and readable `biosketch.md`. The program supports offline inputs using `--record` or `--biosketch`, and optional overrides. Do not commit ORCID access tokens.

## Useful commands

```bash
srp lint 0000-0003-4820-7951
srp export 0000-0003-4820-7951 --format bibtex > refs.bib
srp export 0000-0003-4820-7951 --template erc
srp wrapped 0000-0003-4820-7951 --year 2025
srp card 0000-0003-4820-7951 -o card.svg
srp heatmap 0000-0003-4820-7951 -o heatmap.svg
```

Use `--sandbox` for the ORCID sandbox. Consider ORCID's API terms and retry limits before automation.

## Embedding

A framework-neutral Web Component can display an existing published biosketch JSON with a search-ready works list and provenance. Group snapshots use a separate `<srp-group>` component.

See the repository's established technical guides:

- [Website integration](https://github.com/dhuzard/science-record-player/blob/main/docs/website-integration.md)
- [Group workflow and API](https://github.com/dhuzard/science-record-player/blob/main/docs/group-workflow-api.md)
- [Local network pilot](https://github.com/dhuzard/science-record-player/blob/main/docs/network-pilot.md)
- [Hosting and authentication](https://github.com/dhuzard/science-record-player/blob/main/docs/gcp-hosting.md)
- [Private Teams design and deployment status](https://github.com/dhuzard/science-record-player/blob/main/docs/team-workspaces.md)
- [Roster assertion contract](https://github.com/dhuzard/science-record-player/blob/main/docs/roster-assertions.md)

## Test

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
node --test web/srp-biosketch.test.mjs web/srp-group.test.mjs web/rename-compat.test.mjs web/network/app.test.mjs web/playground/digest.test.mjs web/playground/auth.test.mjs web/playground/teampack.test.mjs
```

Firestore rules/emulator tests and the token-exchange service have independent test commands documented in the repository.

## Build this Sphinx guide

```bash
python -m pip install -r docs/requirements.txt
python -m sphinx -b html -n -W --keep-going docs/source docs/_build/html
```

The published documentation is intended for scientists first; the existing detailed engineering files remain source-of-truth for implementation and deployment.
