# Backlog

Tracked feature backlog for `orcid-biosketch`. Every item has a stable ID, an
explicit status, and a revision history. Status changes are appended to the
[Change log](#change-log) at the bottom of this file rather than overwritten, so
the evolution of the backlog stays auditable in the same way generated outputs
are: **the git history is the record, this file is the index.**

## Conventions

| Field | Meaning |
|---|---|
| **ID** | Stable identifier. `KF-*` killer features, `FUN-*` playful reuses, `INF-*` infrastructure. IDs are never reused. |
| **Status** | `planned` → `in-progress` → `in-review` → `done`. Also `deferred` and `dropped`. |
| **Priority** | `P0` blocks adoption, `P1` high leverage, `P2` valuable, `P3` opportunistic. |
| **Owner** | Who is implementing. `—` when unclaimed. |
| **Files** | Primary files the item owns, to keep parallel work conflict-free. |

### Design rule (applies to every item)

> ORCID supplies structured assertions; the researcher controls narrative and
> selection.

No item may invent, infer, or rewrite a scientific credential. Enrichment from
non-ORCID sources must be labelled per field with its origin. Playful outputs
(`FUN-*`) are re-presentations of asserted facts only — they never fabricate.

---

## Summary

| ID | Title | Priority | Status | Owner |
|---|---|---|---|---|
| KF-01 | Complete the ORCID activities surface | P0 | in-progress | agent/core-surface |
| KF-02 | Full work records via the bulk works endpoint | P1 | planned | — |
| KF-03 | Citation and funder-format exporters | P0 | in-progress | agent/exporters |
| KF-04 | Per-field enrichment with source labelling | P1 | planned | — |
| KF-05 | `lint` — ORCID record quality report | P1 | in-progress | agent/lint |
| KF-06 | Assertion trust layer | P2 | planned | — |
| KF-07 | Lab / multi-researcher mode | P2 | planned | — |
| KF-08 | Change feed and publication Atom feed | P2 | planned | — |
| KF-09 | Agent-facing surface (MCP + well-known) | P2 | planned | — |
| INF-01 | Fetch robustness, offline input, iD validation | P0 | in-progress | session |
| INF-02 | CLI subcommand architecture | P0 | in-progress | session |
| FUN-01 | Academic Wrapped | P2 | in-progress | agent/fun |
| FUN-02 | ORCID trading card | P3 | in-progress | agent/fun |
| FUN-03 | Publication contribution heatmap | P3 | in-progress | agent/fun |
| FUN-04 | Career sonification (MIDI) | P3 | planned | — |
| FUN-05 | Conference badge / vCard / email signature | P2 | planned | — |
| FUN-06 | `fortune` — a paper of your own in your shell | P3 | in-progress | agent/fun |
| FUN-07 | Collaborator distance | P3 | deferred | — |
| FUN-08 | Deterministic career poster | P3 | deferred | — |
| FUN-09 | Academic family tree | P3 | deferred | — |

---

## KF-01 — Complete the ORCID activities surface

- **Priority** P0 · **Status** in-progress · **Owner** agent/core-surface · **Rev** r2
- **Files** `src/orcid_biosketch/core.py`, `schema/biosketch.schema.json`, `tests/`

`build_biosketch` currently reads only `person`, `employments`, `educations` and
`works` from `activities-summary`. The remaining sections are dropped entirely.
Funding and service are what make a document a *biosketch* rather than a
publication list — no funder template can be filled without them.

**Acceptance criteria**
- [ ] Parse `fundings`, `peer-reviews`, `distinctions`, `memberships`,
      `services`, `qualifications`, `invited-positions`, `research-resources`.
- [ ] `_affiliations()` generalised across the five affiliation-shaped sections.
- [ ] Funding retains amount, funder, grant number and external IDs.
- [ ] Peer review aggregated per reviewer group with review counts.
- [ ] Schema updated; every new section documented and validated.
- [ ] Markdown and JSON-LD renderers surface the new sections.
- [ ] Sections absent from a record degrade to empty lists, never `KeyError`.

**Notes** — Peer review is the only machine-readable record of academic
invisible labour that exists anywhere. Surface it prominently.

---

## KF-02 — Full work records via the bulk works endpoint

- **Priority** P1 · **Status** planned · **Owner** — · **Rev** r1
- **Files** `src/orcid_biosketch/core.py`
- **Blocked by** INF-01 (retry/backoff needed before multi-request fetching)

`_works()` reads work-summary groups only, so outputs contain **no authors**. A
biosketch whose publications have no author list cannot be pasted into a CV.
`GET /v3.0/{id}/works/{putcodes}` accepts up to 100 comma-separated put-codes
per request and returns contributors, abstract and language.

**Acceptance criteria**
- [ ] Batch put-codes 100 at a time; whole record in a small number of requests.
- [ ] Contributors normalised to ordered author lists with roles and ORCID iDs.
- [ ] Opt-out flag for callers who want the cheap summary-only fetch.
- [ ] Degrades to summary data when the detail fetch fails.

---

## KF-03 — Citation and funder-format exporters

- **Priority** P0 · **Status** in-progress · **Owner** agent/exporters · **Rev** r2
- **Files** `src/orcid_biosketch/exporters.py` (new), `tests/test_exporters.py`

`render_markdown` is the only renderer. The adoption argument is not "a nicer
web page" — it is removing four hours of formatting the night before a grant
deadline.

**Acceptance criteria**
- [ ] CSL-JSON export, valid against the CSL-JSON item schema.
- [ ] BibTeX export with stable, collision-free citation keys and correct escaping.
- [ ] RIS export.
- [ ] Funder templates (NIH, ERC, Horizon) as data files, not hardcoded, so a
      new format arrives as a contributed template rather than a code change.
- [ ] Every exporter is a pure function of the biosketch contract.

---

## KF-04 — Per-field enrichment with source labelling

- **Priority** P1 · **Status** planned · **Owner** — · **Rev** r1
- **Files** `src/orcid_biosketch/enrich.py` (new)

Enrichment from OpenAlex/Crossref/DataCite, labelled **per field** rather than
per record, so that ORCID-asserted and externally-derived values remain
distinguishable in the output. This is what keeps the design rule intact once
external data enters the pipeline.

**Acceptance criteria**
- [ ] Each enriched value carries its originating source.
- [ ] An ORCID assertion is never overwritten by an external source.
- [ ] Citation counts, open-access status and venue metadata.
- [ ] Retraction check against Crossref / Retraction Watch, surfaced loudly.
- [ ] Fully optional; the tool works offline without it.

---

## KF-05 — `lint`: ORCID record quality report

- **Priority** P1 · **Status** in-progress · **Owner** agent/lint · **Rev** r2
- **Files** `src/orcid_biosketch/lint.py` (new), `tests/test_lint.py`

Score a record and say exactly what to fix. The only item here with standalone
reach: useful to people who will never generate a biosketch, which is precisely
what draws them into the rest of the tool.

**Acceptance criteria**
- [ ] Checks: missing DOIs, missing publication dates, missing venue, empty
      biography, no keywords, no funding, orgs lacking ROR/disambiguation,
      self-asserted-only works, duplicate work groups, stale record.
- [ ] Weighted score with a documented, reproducible rubric.
- [ ] Human-readable report and machine-readable JSON.
- [ ] shields.io-compatible badge endpoint JSON for READMEs.
- [ ] Non-zero exit under a configurable threshold, for CI use.

---

## KF-06 — Assertion trust layer

- **Priority** P2 · **Status** planned · **Owner** — · **Rev** r1
- **Files** `src/orcid_biosketch/core.py`, `web/orcid-biosketch.js`

`_source()` already captures who asserted each work and nothing downstream uses
it. Render the distinction between self-asserted and publisher/institution-
asserted claims. Near-zero cost, and consistent with the provenance thesis.

**Acceptance criteria**
- [ ] Each work classified `self-asserted` / `third-party-asserted`.
- [ ] Trust marker rendered in the web component and the PDF export.
- [ ] Classification logic documented and covered by tests.

---

## KF-07 — Lab / multi-researcher mode

- **Priority** P2 · **Status** planned · **Owner** — · **Rev** r1

One config, N ORCIDs → a team page with deduplicated shared publications and a
collaboration graph. Institutes and labs are the adoption unit; individuals are
a one-person market.

**Acceptance criteria**
- [ ] Config accepts a list of ORCID iDs with per-member overrides.
- [ ] Shared publications deduplicated by DOI across members.
- [ ] Team-level JSON contract and web component mode.
- [ ] Sync workflow handles N records within API rate limits.

---

## KF-08 — Change feed and publication Atom feed

- **Priority** P2 · **Status** planned · **Owner** — · **Rev** r1

The README's pitch is that git commits create an auditable history, but nothing
reads that history back. Render it, and the repository becomes subscribable.

**Acceptance criteria**
- [ ] `CHANGELOG.md` generated from the diff between syncs.
- [ ] Atom feed of new publications.
- [ ] Sync workflow publishes both.

---

## KF-09 — Agent-facing surface

- **Priority** P2 · **Status** planned · **Owner** — · **Rev** r1

An MCP server exposing the biosketch as tools, plus
`/.well-known/researcher.jsonld` and `llms.txt`. The step from
machine-*readable* to machine-*actionable*.

**Acceptance criteria**
- [ ] MCP server with `get_works`, `get_funding`, `find_expertise`.
- [ ] Well-known JSON-LD document emitted alongside generated outputs.
- [ ] `llms.txt` summarising the record for agent consumption.

---

## INF-01 — Fetch robustness, offline input, iD validation

- **Priority** P0 · **Status** in-progress · **Owner** session · **Rev** r2
- **Files** `src/orcid_biosketch/core.py`, `src/orcid_biosketch/cli.py`

`fetch_orcid_record` has no retries, no caching and no rate-limit handling. The
CLI cannot read a saved record from disk — the test suite can, via
`tests/fixture.json`, but users cannot. A mistyped iD becomes a confusing HTTP
error rather than a clear message.

**Acceptance criteria**
- [ ] MOD 11-2 checksum validation of ORCID iDs with a clear error.
- [ ] `--record FILE` for offline and CI runs.
- [ ] Retry with exponential backoff; explicit rate-limit handling.
- [ ] ORCID sandbox base URL supported for contributor testing.
- [ ] Network failures produce actionable messages, not tracebacks.

---

## INF-02 — CLI subcommand architecture

- **Priority** P0 · **Status** in-progress · **Owner** session · **Rev** r2
- **Files** `src/orcid_biosketch/cli.py`

The CLI is a single flat command. Every feature above needs a verb.

**Acceptance criteria**
- [ ] Subcommands: `generate`, `lint`, `export`, `wrapped`, `fortune`, `badge`.
- [ ] `orcid-biosketch <ORCID>` keeps working unchanged (back-compat).
- [ ] Shared options factored into a common parent parser.

---

## FUN-01 — Academic Wrapped

- **Priority** P2 · **Status** in-progress · **Owner** agent/fun · **Rev** r2
- **Files** `src/orcid_biosketch/fun.py` (new)

Spotify-style year in review: top venue, most prolific month, longest gap,
keyword drift, co-authors met for the first time. Highest shareability per line
of code in the entire backlog. Ship in December.

**Acceptance criteria**
- [ ] Terminal, JSON and shareable-card outputs.
- [ ] Every statistic derived from asserted data; nothing invented.
- [ ] Graceful with sparse records — a two-paper year still produces something
      kind rather than something bleak.

---

## FUN-02 — ORCID trading card

- **Priority** P3 · **Status** in-progress · **Owner** agent/fun · **Rev** r2

A printable stat card: years active as HP, output count as attack, a "special
ability" drawn from the record's own keywords. QR to the ORCID record.

**Acceptance criteria**
- [ ] Self-contained SVG, print-ready, no external assets.
- [ ] Stats traceable to record fields.

---

## FUN-03 — Publication contribution heatmap

- **Priority** P3 · **Status** in-progress · **Owner** agent/fun · **Rev** r2

The GitHub green-squares grid for publication dates. Instantly legible, and
quietly humane: it shows the fallow years that polished CVs hide.

**Acceptance criteria**
- [ ] Self-contained SVG, readable in light and dark contexts.
- [ ] Sensible with decade-spanning records.

---

## FUN-04 — Career sonification

- **Priority** P3 · **Status** planned · **Owner** — · **Rev** r1

Publication dates to notes, venues to instruments, output counts to velocity;
emit a MIDI file. "Here is what my postdoc sounds like."

**Acceptance criteria**
- [ ] Standard MIDI written from the standard library, no dependencies.
- [ ] Deterministic: the same record always yields the same file.

---

## FUN-05 — Conference badge, vCard and email signature

- **Priority** P2 · **Status** planned · **Owner** — · **Rev** r1

Boring-useful disguised as fun, and the item people would use weekly: A6 badge
with QR and top outputs, a vCard, and an HTML email signature.

**Acceptance criteria**
- [ ] Print-ready badge at A6; QR generated without a runtime dependency.
- [ ] Valid vCard 4.0 including the ORCID iD.

---

## FUN-06 — `fortune`

- **Priority** P3 · **Status** in-progress · **Owner** agent/fun · **Rev** r2

Print a random one of your own paper titles in your shell. Twenty lines, pure
joy.

**Acceptance criteria**
- [ ] Reads a generated biosketch; no network access at call time.
- [ ] Fast enough for a shell startup file.

---

## FUN-07 — Collaborator distance · deferred

Erdős-number-style distance between two ORCID iDs via OpenAlex coauthorship.
**Deferred**: depends on KF-04's enrichment client.

## FUN-08 — Deterministic career poster · deferred

Generative art seeded from the ORCID digits and work titles; the same iD always
yields the same artwork. **Deferred**: no dependency, purely a question of
sequencing after the P0/P1 work.

## FUN-09 — Academic family tree · deferred

Chain `educations` across ORCID iDs to reconstruct advisor lineages.
**Deferred**: needs KF-07's multi-record fetching.

---

## Change log

Append-only. Newest entries at the bottom. One line per status or scope change.

| Date | ID | Change | From → To |
|---|---|---|---|
| 2026-08-31 | — | Backlog created from feature review of `main` @ `9dff19b` | — |
| 2026-08-31 | KF-01…KF-09 | Killer features entered from repository analysis | — → planned |
| 2026-08-31 | INF-01, INF-02 | Infrastructure prerequisites identified while scoping KF-02/03/05 | — → planned |
| 2026-08-31 | FUN-01…FUN-06 | Playful reuses entered | — → planned |
| 2026-08-31 | FUN-07, FUN-08, FUN-09 | Sequenced behind enrichment and multi-record work | — → deferred |
| 2026-08-31 | KF-01 | Assigned to subagent; owns core.py, schema, core tests | planned → in-progress |
| 2026-08-31 | KF-03 | Assigned to subagent; owns exporters.py + templates/ | planned → in-progress |
| 2026-08-31 | KF-05 | Assigned to subagent; owns lint.py | planned → in-progress |
| 2026-08-31 | FUN-01, FUN-02, FUN-03, FUN-06 | Assigned to one subagent; owns fun.py | planned → in-progress |
| 2026-08-31 | INF-01, INF-02 | Retained by session; sequenced after KF-01 to keep core.py single-owner | planned → in-progress |
| 2026-08-31 | KF-01 | schema_version raised to 0.2.0 as part of the contract extension | scope |
