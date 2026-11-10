# Branding and rename — ORCID's answer and our decisions

## Status (10 November 2026)

**ORCID declined permission for the current branding.** The ORCID Communications & Brand Team replied on 9 November 2026. They were positive about the project and invited us to send the updated link once it is rebranded; they may help promote it in their 2027 researcher-outreach campaigns. They are **not** able to approve the name "ORCID Playground", the `orcid-playground` hostname, or the current visual identity. A rename is required.

Do not launch, announce or record videos under the old name. Do not describe any ORCID approval until ORCID has reviewed the rebranded app in writing.

## What ORCID asked for

| Request | What it means for us | Status |
|---|---|---|
| **Name and hostname**: "ORCID" must not be the leading identifier. They suggested "[ProjectName]: An Open-Source Playground for ORCID Records" or "[ProjectName] by Neuronautix". | Choose a distinct name; move to a matching hostname. | Name chosen: **Science Record Player (SRP)**, tagline "Publish or Play". Hostname pending: **INF-13** |
| **Distinct visual identity**: the layout and green palette look too much like ORCID. | New colour scheme, typography and icon. | Done: muted pink / aubergine palette, new ✦ rounded-square icon, new heading typeface (**INF-12**) |
| **Prominent ownership**: the header must say the app is developed and maintained independently by Damien Huzard / Neuronautix under the MIT license. | Ownership line in every page header. | Done (**INF-12**) |
| **Prominent disclaimer**, verbatim: *"This is an independent open-source project and is not affiliated with, sponsored by, or endorsed by ORCID."* | Visible banner on every page, not fine print. | Done on all hosted pages, network page, docs announcement bar, README and video cards (**INF-12**) |
| **Fair use and attribution**: compatibility with ORCID and crediting the ORCID Public API are welcome, with *"ORCID® is a registered trademark of ORCID, Inc."* | Keep "works with public ORCID records"; use ® attribution. | Done: footers now use ®, not ™ (**INF-12**) |

## Decisions taken (10 Nov 2026)

1. **Name: Science Record Player (SRP)**, chosen 10 Nov 2026. The pun: your science *record*, played like a vinyl in many formats (biosketch, card, heatmap, Wrapped, fortune, exports). **"Publish or Play"** is used as the tagline and description line. The name is set in one place: `config/brand.json`. The site build (`scripts/build_site.py`), the Sphinx docs (`{{ brand }}`) and the demo title cards all read it. A future rename means editing that file, the README title and the launch copy.
2. **Palette: muted pink.** Accent `#e2b4c0` (dusty rose), brand `#3a2737` (aubergine), paper `#faf6f7`, ink `#2b2230`. All former greens were shifted to the rose hue with their lightness preserved. The new icon is a rounded square, not a circle.
3. **URLs stay for now.** `orcid-playground-889.web.app` and the GitHub repository keep working until the new hostname exists (INF-13; suggested `science-record-player.web.app` or a custom domain, and repository `science-record-player`). ORCID explicitly asked for the hostname to change, so this is temporary and must be done before sending them the link again.
4. **Code names: follow-up.** `orcid_biosketch`, `orcid-biosketch`, `<orcid-biosketch>` and `<orcid-group>` stay as they are for now. They will be renamed with aliases later (INF-14).
5. **Internal identifiers unchanged.** Storage keys, cache names and file-format IDs (`orcid-playground-workspace`, `orcid-playground-team-group`, `orcid-playground/roster-assertion`) are not shown to users. Changing them would break existing backups and browser data. The downloaded backup is now named `research-workspace-<date>.json`.

## Name shortlist considered (puns that show the features)

Chosen: a variant of **Record Player**, as **Science Record Player (SRP)**, with **Publish or Play** as the tagline. Availability still to be checked. Search EUIPO, INPI and USPTO, plus domains, GitHub, PyPI and npm, before choosing.

| Candidate | The pun | Features it evokes | Notes |
|---|---|---|---|
| **Record Player** | Your *research record*, played like a vinyl | One record "played" as biosketch, card, heatmap, Wrapped, fortune, exports | Strongest fit with "playground"; "Record Player by Neuronautix" reads well. Common phrase, so a weaker trademark |
| **Publish or Play** | "Publish or perish" | Serious outputs (funder biosketches, citations) and playful ones (Wrapped, cards) | Memorable; tells the two-sided story |
| **Curriculum Vibe** | Curriculum vitae | CVs and biosketches, plus Wrapped and fortune "vibes" | Very fun; a bit less serious for grant use |
| **Works Wonders** | ORCID calls outputs "works" | Does wonders with your works: record check, exports, groups | Subtle ORCID nod without the trademark |
| **Biblio-file** | Bibliography + file | BibTeX, RIS, CSL JSON, JSON-LD exports | Narrower: emphasizes exports over network and fun |
| **Full House** | Full deck of cards / full team | Trading-card deck, groups, team biosketch | Good for the group features; less for individuals |
| **Paper Trail** | Trail of papers | Per-field provenance, record check, feed | Very crowded name |

## Next steps (owner)

1. ~~Pick the name~~ (done). Check availability of "Science Record Player" / "SRP" (EUIPO, INPI, USPTO, domains, GitHub, PyPI, npm). SRP is a common acronym; use it as a short form, not the main brand.
2. ~~Set it in `config/brand.json`, the README title and the launch copy~~ (done).
3. Create the Firebase site `science-record-player` and follow the runbook in `docs/gcp-hosting.md` § Moving to science-record-player.web.app. The old address forwards to the new one without losing browser-local workspaces.
4. Reply to ORCID with the new link and screenshots.

## Technical migration checklist (INF-13)

1. Search all displayed brand strings (Studio, Network, Groups, Teams, Docs, Sphinx, README, metadata, feedback and video overlays); update them without changing facts or scientific warnings.
2. Prefer a **new Firebase Hosting site/project or custom domain** with a neutral hostname. Configure OAuth redirect URIs for the new origin and update auth host allow-lists, CSP, service worker cache identity, links, references, CI deploy secrets and video pipeline. Do not put secrets in docs.
3. Keep a publicly understandable redirect/deprecation period from the legacy address **only if ORCID permits that transitional use**. Avoid leaking personal team data in URL redirects.
4. Consider a GitHub repository rename (GitHub may redirect old links) only after changing citations and pinned URLs; verify actual redirects. Don't rename Python imports or CLI commands without compatibility aliases and a documented deprecation cycle.
5. Regenerate icons and all video title cards. Label the project “Independent; not an official ORCID service”. Apply trademark attribution to landing pages using ORCID-specific subdomains.
6. Verify the built client, docs, service worker, CI, authentication, public API calls, and static widgets end to end on the new URL.
7. Announce the new canonical URLs only when deployed and checked. Do not imply permission via a disclaimer alone.

**No rename, DNS, OAuth, or Firebase project changes are performed by this document.**

## Original request (sent before ORCID's answer, kept for the record)

**Subject:** Request for guidance and written permission — independent open-source “ORCID Playground” app and hostname

Hello ORCID Communications / Brand team,

I am the creator of an independent, MIT-licensed open-source research project currently called “ORCID Playground”:
- Working demo: https://orcid-playground-889.web.app/
- Source repository: https://github.com/dhuzard/orcid-playground

It reads **public ORCID record assertions** and allows researchers to explore their biosketch, inspect a record-quality report, download bibliographic and structured data, and experiment with a browser-local research network and public group summaries. It does not write to ORCID records or claim to verify scientific identities, authorships or group membership. The application already states that it is not an official ORCID service.

Before a broader community invitation and demonstration video, I would like to comply fully with your brand guidance. May we have your **written assessment and, if appropriate, permission** regarding:

1. Use of **“ORCID Playground”** as the independent application's name.
2. Use of the Firebase hostname **`orcid-playground-889.web.app`**.
3. The independence statement, attribution/marking and existing distinct “o.” icon (and whether you recommend any changes).
4. Any relevant requirements concerning use of the public API or demonstration of public records.

I understand if you would prefer a unique non-ORCID product name; we can rebrand the application while continuing to describe ORCID as its data source. I would welcome suggestions, including whether a disclaimer or prominent link should change.

The live site is a visual mockup of the current implementation; I can provide screenshots and a draft of the proposed new communications materials. I will not describe any permission as granted until I receive it in writing.

Kind regards,
Damien Huzard
Project creator / Neuronautix
