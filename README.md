# ORCID Biosketch

Generate a researcher-controlled, provenance-aware biosketch from a public ORCID record. The tool creates stable JSON, Schema.org JSON-LD and Markdown outputs that can be consumed by personal websites, institutional profiles and research agents.

The central design rule is simple: **ORCID supplies structured assertions; the researcher controls narrative and selection.** The tool does not silently invent or rewrite scientific credentials.

## Quick start

```bash
python -m pip install -e .
orcid-biosketch 0000-0003-4820-7951 \
  --config config/biosketch.json \
  --output generated
```

Outputs:

- `generated/biosketch.json` — canonical normalized record
- `generated/biosketch.jsonld` — Schema.org `Person`
- `generated/biosketch.md` — website- and CV-ready Markdown

Only public ORCID data are retrieved. An optional `ORCID_ACCESS_TOKEN` environment variable is supported; never commit access tokens.

## Automatic synchronization

The included GitHub Actions workflow refreshes the generated files daily and commits only when the ORCID-derived output changes. The generated timestamp is derived from ORCID's record modification time, preventing meaningless daily commits. It can also be run manually from **Actions → Synchronize ORCID biosketch → Run workflow**.

Git commits create an auditable history. ORCID webhooks are not used because they require premium ORCID membership; daily polling is the free, practical synchronization mechanism.

## Embed in a website

Load the web component and point it to any published `biosketch.json`:

```html
<script type="module" src="https://cdn.jsdelivr.net/gh/dhuzard/orcid-biosketch@main/web/orcid-biosketch.js"></script>
<orcid-biosketch
  src="https://raw.githubusercontent.com/dhuzard/orcid-biosketch/main/generated/biosketch.json"
  works="5">
</orcid-biosketch>
```

For static Jekyll, Hugo, Quarto or MyST sites, consuming the generated Markdown or JSON at build time is preferable: it is faster, versioned and does not depend on client-side JavaScript.

## Researcher-controlled overrides

Pass a JSON document with `--config`. It is recursively merged onto the normalized record. This is intended for a headline, approved narrative variants and explicit publication-selection metadata. Overridden values are marked in provenance.

```json
{
  "person": {
    "headline": "Behavioral neuroscientist and FAIR metadata consultant"
  }
}
```

## Data quality and provenance

- ORCID visibility rules are respected: private and trusted-party-only information is not available through the public endpoint.
- Each work and affiliation retains its ORCID source and put-code where available.
- Duplicate ORCID work groups are represented by their preferred summary.
- ORCID is not a complete CV. Software, supervision, project narratives and selected-output policies usually require researcher-controlled additions.
- The generated timestamp reflects ORCID's record modification time, so identical source records produce identical outputs.

## Development

```bash
python -m pip install -e ".[dev]"
pytest -q
```

## Roadmap

- Crossref/OpenAlex enrichment without overwriting ORCID assertions
- Named short, medium and long approved biography variants
- CSL-JSON, DOCX and PDF exporters
- Selection rules for works and grants
- Jekyll, Hugo, Quarto and MyST integration examples
- Optional ORCID OAuth and premium webhook adapter

## License

MIT
