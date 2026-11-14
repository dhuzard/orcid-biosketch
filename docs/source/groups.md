# Group view — visualize public scientific connections

Use [Group view](https://science-record-player.web.app/group/) when you want a **shareable visualization** based on several public ORCID records, without publishing local contact notes or roles.

## Create a group link

1. Give the group a name.
2. Paste up to 50 public ORCID iDs or ORCID URLs.
3. Preview the link, then choose **Read the public records**.
4. Copy the resulting URL. Its fragment contains the group name and ORCID iDs. The listed researchers have **not** confirmed this grouping or their membership.

Each viewer reads public ORCID records in their browser on request. The link does not encode your local roster annotations, requests or selected project works.

## Explore the outputs

- **Shared-DOI graph** (formerly “Collaboration graph”): an edge appears when *both* public records assert the same DOI. Selecting an edge shows the DOIs supporting it.
- **Shared outputs and bibliography:** group works merged using DOI matches where available.
- **Record health:** inspect member-specific quality findings and common improvements; export a report.
- **Funder-format team biosketch:** an editable draft, not an approved or funder-compliant application.
- **Group Wrapped, card deck and heatmap:** visual summaries based on available public assertions.
- **Embed:** download a snapshot and embed the `<srp-group>` web component on a lab website. The snapshot is static until replaced.

**Important scientific distinction:** two records sharing the same DOI is evidence of a shared output assertion, **not proof of a collaboration relationship**, CRediT role, institutional membership or consent. DOI-less outputs may not be linked.

## Locally curated groups vs public links

The **Research network** tracks your own roster, roles, project outputs and requests. These are local annotations and never automatically become verified public group statements.

The **Encrypted team package** feature can transfer one curated group with a chosen password. The file may contain sensitive local annotations; send its password via a separate channel. Anyone holding both can decrypt it. This is not the same as a member-confirmed private cloud Team workspace.

## Private Teams feature

The codebase contains invite-only Team workspaces and personal cloud sync, with ORCID sign-in and access-control rules. As documented in November 2026, activation of the public cloud backend is still pending; **do not advertise this as a live feature until an end-to-end public deployment test succeeds**.

See [Trust and privacy](trust.md), and the maintainer's [technical Team workspace design](https://github.com/dhuzard/science-record-player/blob/main/docs/team-workspaces.md).
