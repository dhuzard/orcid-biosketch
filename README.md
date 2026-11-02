# ORCID Playground

**Your ORCID record can do more.** Explore public research profiles, inspect record quality, reuse publication data and experiment with a research network—without installing software.

**[Try the Playground](https://orcid-playground-889.web.app/)** · **[Read documentation](https://orcid-playground-889.web.app/docs/)** · **[Send feedback](https://orcid-playground-889.web.app/feedback/)** · **[Five-minute guide](docs/source/getting-started.md)** · **[Sphinx documentation source](docs/source/index.md)** · **[Suggest a feature](https://github.com/dhuzard/orcid-playground/issues/new/choose)**

> **Independent open-source project, not an official ORCID service.** ORCID data are public assertions, not independently verified credentials. The application does not silently invent scientific outputs, affiliations or group membership.

## Try it in two minutes

1. Open the [live Studio](https://orcid-playground-889.web.app/).
2. Select **The maintainer's profile (stored, offline)**, or paste any public ORCID iD. No sign-in is needed to explore public records.
3. Open **Record check**, explore the works table and download a **BibTeX**, **RIS**, **JSON-LD** or Markdown export.
4. Try the [research network with labelled sample data](https://orcid-playground-889.web.app/network/?sample=1#groups). Experiment with following people, private contact tags and a project group.
5. Tell us **what would be useful for your research** through a [scientist feedback issue](https://github.com/dhuzard/orcid-playground/issues/new/choose). You can use the in-app email feedback form without a GitHub account; GitHub issues remain available for developers.

## What can you do?

| Place | Features | Start |
| --- | --- | --- |
| **Studio** | Searchable researcher profile and works; **Record check** with actionable suggestions; editable **NIH / ERC / Horizon draft biosketches**; BibTeX, RIS, CSL JSON, normalized JSON, JSON-LD and Markdown exports | [Explore a record](https://orcid-playground-889.web.app/) |
| **Visualizations** | SVG trading card and publication heatmap, career **Wrapped**, and **Fortune** from recorded titles | [Studio](https://orcid-playground-889.web.app/) |
| **Research network** | Feed with filters, People, Saved works, **Contacts** with conference-context tags/notes/follow-ups, curated **Groups**, project-output selection, requests and a team pack | [Try sample data](https://orcid-playground-889.web.app/network/?sample=1#groups) |
| **Public Group view** | Share a link containing a group name and public ORCID iDs; inspect DOI-based links, shared works, record health, team biosketch drafts, Group Wrapped, card deck, heatmap, bibliography and website embed | [Create a group link](https://orcid-playground-889.web.app/group/) |
| **Local saving and sharing** | Workspace download/restore; browser-local research network; password-encrypted transfer package for a curated group; installable/offline-capable web app | [Research network guide](docs/source/research-network.md) |
| **Developers** | Python package/CLI, structured provenance, deterministic exports, and framework-neutral biosketch and group Web Components | [Developer guide](docs/source/developers.md) |

**Not yet confirmed active on the public site:** invite-only **private cloud Team workspaces** and personal cloud sync. Code, access rules and tests have been added, but deployment notes still describe an unfinished production activation. These are *not* prerequisites for using Studio or the browser-local network. See [availability and privacy details](docs/source/trust.md).

## The scientific boundaries matter

- **ORCID provides public assertions.** A valid iD or a public record does not independently verify the person's identity, affiliations, authorship, funding or project membership.
- **“Connected” in Group view means both public records list the same DOI.** It is not independent evidence that two people collaborated, held specific roles or agreed to a group listing.
- **Funder-format exports are drafts.** Verify the content and current official requirements before use.
- **Your local notes are not public ORCID data.** The research-network workspace stays in your browser by default; a downloaded backup or encrypted team package contains local annotations, so handle it carefully.
- **Not everything works offline.** Cached application code and stored data can be usable offline after a visit; live public ORCID reads need a connection.

See [Provenance, limits and privacy](docs/source/trust.md) for precise data flows and caveats.

## Help shape the next version

We especially welcome feedback from **individual scientists, lab and consortium coordinators, research software engineers, data stewards and librarians**.

No code is necessary. Try a real task (or clearly labelled sample data), then tell us what was confusing, which result needs correction, and what would make the tool worth using again.

**[Send scientist feedback without GitHub](https://orcid-playground-889.web.app/feedback/)** · [Open a GitHub issue](https://github.com/dhuzard/orcid-playground/issues/new/choose) · [How to contribute](CONTRIBUTING.md) · [Existing backlog](BACKLOG.md)

Scientific correctness, provenance and privacy concerns are prioritized over decorative additions.

## For Python users

The package and executable remain named `orcid_biosketch` and `orcid-biosketch`:

```bash
python -m pip install -e .

orcid-biosketch generate 0000-0003-4820-7951 \
  --config config/biosketch.json --output generated
orcid-biosketch lint 0000-0003-4820-7951
orcid-biosketch export 0000-0003-4820-7951 --format bibtex > refs.bib
orcid-biosketch export 0000-0003-4820-7951 --template nih
orcid-biosketch wrapped 0000-0003-4820-7951 --year 2025
```

Generated files include `biosketch.json` (provenance-aware), `biosketch.jsonld` (Schema.org) and `biosketch.md`. The CLI also supports `card`, `heatmap`, `fortune`, `badge`, offline `--record` / `--biosketch` input, `--sandbox`, and optional public-record details. Do not commit access tokens.

Local SQLite research-network pilot:

```bash
python -m orcid_biosketch.network --port 8877 --data .local/network.sqlite3
```

Open `http://127.0.0.1:8877`. The pilot is local-only and has no shared logins or verified group membership. See [the local network guide](docs/network-pilot.md).

### Embedding in your website

The `<orcid-biosketch>` Web Component reads a published `biosketch.json` and supports biography, a searchable works table, source details and print/PDF export; the `<orcid-group>` component reads a published group snapshot. Follow the [website integration guide](docs/website-integration.md). The static snapshot does not update itself until regenerated.

### Build, tests and documentation

```bash
python -m pip install -e ".[dev]"
python -m pytest -q

python -m pip install -r docs/requirements.txt
python -m sphinx -b html -n -W --keep-going docs/source docs/_build/html
```

Sphinx is built from [docs/source](docs/source/index.md) and deployed with the playground at [the hosted documentation](https://orcid-playground-889.web.app/docs/). A separate video-production workflow is proposed in [PR #31](https://github.com/dhuzard/orcid-playground/pull/31); the [comprehensive video storyboard](communications/video-storyboard.md) identifies remaining footage and scientific disclaimers.

## License and attribution

[MIT](LICENSE) for repository code. Public ORCID records are subject to their own data policies and visibility settings. ORCID Playground is independent from ORCID, Inc. Refer to the [ORCID public API](https://info.orcid.org/what-is-orcid/services/public-api/) and [brand guidelines](https://info.orcid.org/brand-guidelines/).
