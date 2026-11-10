# Studio — one public record, many outputs

Open [Studio](https://science-record-player.web.app/), enter a public ORCID iD or try the stored profile, and move between its tabs. Results are generated from fields available in the imported record; they are not a substitute for reviewing that record.

## Profile

Explore the researcher's name, biography, affiliations and works. The reusable website component provides a searchable and sortable works table, including type filtering and links to DOI/ORCID records where available.

## Trading card

An SVG card translates record fields into a deliberately playful format: years active, output counts, and keywords. Download the SVG for a conference or lab noticeboard. The card is not an assessment of scientific quality.

## Heatmap

An SVG grid of research outputs over months and years. It visualizes **dates in public records**, not actual working hours, productivity or career interruptions.

## Wrapped

A year-in-review narrative derived from available publications, including activity timing and venue summaries. Both text and structured JSON are downloadable. An empty or sparse year should not be interpreted as a career assessment.

## Fortune

Rediscover a title from the works in the record; generate another choice without adding fabricated content.

## Record check

Read a graded checklist of detectable omissions or inconsistencies, with specific suggested fixes. You can download the report.

**Interpretation:** The score measures this tool's explicit completeness/quality rubric, *not* research merit or a verified scientific identity. A lower score can also reflect sparse or non-public records.

## Funder biosketch

Preview and download Markdown drafts oriented to NIH, ERC and Horizon formats. They use available asserted fields, but **must be checked, completed and adapted to the current funder's official requirements** before submission.

## Citations & data

Download BibTeX, RIS and CSL JSON bibliographies, the normalized biosketch JSON with provenance, Schema.org JSON-LD, or human-readable Markdown. Publication fields may be incomplete and require checking before reuse.

## Data provenance

The public ORCID API provides source assertions. The generated formats distinguish the original public information from approved local overrides in the Python tool. ORCID records can contain duplicates, missing DOIs, and incomplete dates.

For limitations, storage choices and private data boundaries, see [Provenance, limits and privacy](trust.md).

## Going further

The same Python package also provides a command-line interface and an embeddable Web Component for personal/institutional pages. See [Developers and reusable components](developers.md).
