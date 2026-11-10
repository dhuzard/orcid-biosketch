# Provenance, limits and privacy

This project makes **asserted public ORCID data more usable**; it does not claim to establish an independently verified academic identity or scientific contribution.

## What is the source?

- Only fields publicly accessible from ORCID can be retrieved through the public API. Hidden or absent fields may not appear.
- A valid ORCID iD is a syntactically valid identifier, **not proof that the named person, employment, authorship or other assertions are genuine**.
- ORCID record data can contain duplicates, missing identifiers and incomplete dates. Downloads should be reviewed before use in a CV, funding submission or research information system.
- CLI-generated JSON preserves source and override provenance. The project does not deliberately fabricate credentials or fill missing accomplishments with language-model guesses.

## What is—and is not—a collaboration?

A Group view link joins two records **only when the same DOI is listed in both public records**. This documents a shared DOI assertion, not a verified author relationship, real-world collaboration, project participation or consent. Some true colleagues will not be connected if records or DOIs are incomplete.

## Data flow by feature

| Feature | Where information lives | External interactions |
| --- | --- | --- |
| Hosted Studio and public Group view | Computation in your browser; downloaded exports on your device | Public ORCID API when you request a live record; hosted site serves code/runtime |
| Hosted Research network and Contacts | A workspace in your browser (IndexedDB/local browser storage) | Public ORCID API on requested import/refresh |
| Browser workspace backup and encrypted group package | File downloaded to your device | No automatic upload of the file; users control sharing |
| Optional ORCID sign-in | Tab-scoped authentication state | ORCID authorization and public keys |
| Private Teams / personal cloud sync **when activated** | Google Cloud Firestore in an EU region, subject to team access rules | ORCID sign-in, token-exchange endpoint and Firebase/Firestore API |
| Python CLI / local network pilot | Local files and (for the network pilot) a local SQLite database | Optional public ORCID API calls |

**Current release qualification (2 November 2026):** The Teams backend code, access rules and tests exist, but repository deployment notes say the cloud exchange endpoint awaits production activation. Do not assume that private Teams or cloud sync are available on the hosted site without a successful live test. The static hosted network and local/manual backups are distinct.

## What should never be published inadvertently?

- Your workspace backup may include locally entered **contact notes, tags, meeting dates, roles, group selections, requests and follow-ups**.
- Password-protected encrypted group packages can be decrypted by anyone with **both** the package and its password. The file is not proof of member consent or a secure identity-verification mechanism.
- Shareable Group view URLs disclose the **group name and public ORCID iDs** to those who receive the URL; they deliberately exclude local annotations.
- Static embeddable group snapshots are public to anyone accessing the website where you post them.

## Independence and attribution

**{{ disclaimer }}** {{ brand }} is developed and maintained independently by {{ owner }} under the {{ license }} license. It does not write to public ORCID records. {{ trademark }} Refer to [the official ORCID Public API documentation](https://info.orcid.org/what-is-orcid/services/public-api/) and [ORCID brand guidance](https://info.orcid.org/brand-guidelines/) for terms and proper attribution.

For a methodological discussion or to report a misleading assertion, please [send feedback](feedback.md).
