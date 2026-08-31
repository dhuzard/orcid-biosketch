# ORCID Biosketch

Generate a researcher-controlled, provenance-aware biosketch from a public ORCID record. The tool creates stable JSON, Schema.org JSON-LD and Markdown outputs that can be consumed by personal websites, institutional profiles and research agents.

The central design rule is simple: **ORCID supplies structured assertions; the researcher controls narrative and selection.** The tool does not silently invent or rewrite scientific credentials.

## Quick start

```bash
python -m pip install -e .
orcid-biosketch generate 0000-0003-4820-7951 \
  --config config/biosketch.json \
  --output generated
```

`orcid-biosketch <ORCID>` still generates, as before subcommands existed.

Outputs:

- `generated/biosketch.json` — canonical normalized record
- `generated/biosketch.jsonld` — Schema.org `Person`
- `generated/biosketch.md` — website- and CV-ready Markdown

Only public ORCID data are retrieved. An optional `ORCID_ACCESS_TOKEN` environment variable is supported; never commit access tokens.

## Commands

Every command accepts an ORCID iD, or works offline from `--record` (a saved
ORCID API response) or `--biosketch` (an already-generated `biosketch.json`).

| Command | Purpose |
|---|---|
| `generate` | Write `biosketch.json`, `.jsonld` and `.md` |
| `lint` | Score the record and say what to fix; `--fail-under N` exits non-zero |
| `export` | `--format csl\|bibtex\|ris`, or `--format template --template nih\|erc\|horizon` |
| `wrapped` | A year in review, computed only from asserted data |
| `card` | Printable trading card (SVG) |
| `heatmap` | Publication heatmap (SVG) |
| `fortune` | Print one of your own titles, for a shell startup file |
| `badge` | shields.io endpoint JSON for the lint score |

```bash
orcid-biosketch lint 0000-0003-4820-7951            # what to fix, and why
orcid-biosketch export 0000-0003-4820-7951 --format bibtex > refs.bib
orcid-biosketch export 0000-0003-4820-7951 --format template --template nih
```

ORCID iDs are checksum-validated before any request, so a typo fails
immediately rather than as a confusing 404. Transient failures retry with
exponential backoff and honour `Retry-After`; `--sandbox` targets ORCID's
sandbox API.

## Automatic synchronization

The included GitHub Actions workflow refreshes the generated files daily and commits only when the ORCID-derived output changes. The generated timestamp is derived from ORCID's record modification time, preventing meaningless daily commits. It can also be run manually from **Actions → Synchronize ORCID biosketch → Run workflow**.

Git commits create an auditable history. ORCID webhooks are not used because they require premium ORCID membership; daily polling is the free, practical synchronization mechanism.

## Embed in a website

Load the web component and point it to any published `biosketch.json`:

```html
<script type="module" src="https://cdn.jsdelivr.net/gh/dhuzard/orcid-biosketch@main/web/orcid-biosketch.js"></script>
<orcid-biosketch
  src="https://raw.githubusercontent.com/dhuzard/orcid-biosketch/main/generated/biosketch.json"
  bio="true"
  works="all"
  search="true"
  pdf="true"
  provenance="true">
</orcid-biosketch>
```

The reusable component can display the biography, a searchable publication table, provenance, and an A4 PDF export. It adds no framework dependency and isolates its styling with Shadow DOM.

See the complete [website integration guide](docs/website-integration.md) for plain HTML, Astro, Jekyll/GitHub Pages, Hugo, Quarto and MyST, including browser-time and build-time synchronization.

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

- The contract is `schema_version` 0.2.0, covering funding, peer review,
  distinctions, memberships, services, qualifications, invited positions and
  research resources alongside works and affiliations.
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

## Included website capabilities

- Browser-time loading of the latest synchronized profile
- Configurable biography and work limits
- Publication search, output-type filtering and sorting
- DOI links and visible provenance
- Selectable, searchable A4 PDF biosketch export
- Framework-neutral Web Component
- Build-time JSON, JSON-LD and Markdown alternatives

## Roadmap

Tracked in [BACKLOG.md](BACKLOG.md), which carries status, acceptance criteria
and an append-only change log for every item. Next up:

- Full work records, including authors, via the bulk works endpoint (KF-02)
- Crossref/OpenAlex enrichment, labelled per field so ORCID assertions stay
  distinguishable and are never overwritten (KF-04)
- Assertion trust layer: self-asserted versus publisher-asserted works (KF-06)
- Lab and multi-researcher mode (KF-07)
- Change feed and publication Atom feed (KF-08)
- Named short, medium and long approved biography variants
- Optional ORCID OAuth and premium webhook adapter

## License

MIT
