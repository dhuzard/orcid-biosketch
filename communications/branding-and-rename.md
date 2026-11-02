# ORCID naming review — permission request and reversible rebrand

**Decision status (2 November 2026):** permission **not requested or granted** through this repository. Do not describe the current name as authorized; do not send a public announcement with implied ORCID endorsement.

## What the official guidelines say

ORCID's [Brand Guidelines](https://info.orcid.org/brand-guidelines/) ask third parties **not** to use ORCID in an application, product or website name without prior written permission, and to create distinct branding.

They separately describe *some* ORCID-specific **subdomain** patterns as permitted, provided landing pages link to `orcid.org` and acknowledge the trademark. Thus the **product name** and the **Firebase hostname** require separate assessment; it is inaccurate to assume that every subdomain containing "orcid" is automatically forbidden.

For use outside standard guidance, ORCID asks that you include a **visual mockup** and request written approval. Their official [contact form](https://support.orcid.org/hc/en-us/requests/new) is the recommended route.

The [ORCID team directory](https://info.orcid.org/orcid-team/) lists **Julie Petro, Director of Communications**. Request that the contact-form submission be routed to Communications / Brand; do not guess a personal email address.

## Draft request (paste into ORCID's contact form)

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

## Two-track decision

**Track A — permission granted in writing:** retain the name only for the exact uses authorized, apply requested attribution, review logo/icon, clarify public API terms, and preserve the approval record.

**Track B — rename required or unclear:** choose a distinct name, confirm availability (web, code hosting, app stores and relevant trademark registers, particularly EUIPO/INPI), and use “works with public ORCID records” as descriptive copy. The temporary working label **Research Record Lab** is a placeholder, **not** a trademark-clearance conclusion.

### Technical migration checklist (only after approval of the new name)

1. Search all displayed brand strings (Studio, Network, Groups, Teams, Docs, Sphinx, README, metadata, feedback and video overlays); update them without changing facts or scientific warnings.
2. Prefer a **new Firebase Hosting site/project or custom domain** with a neutral hostname. Configure OAuth redirect URIs for the new origin and update auth host allow-lists, CSP, service worker cache identity, links, references, CI deploy secrets and video pipeline. Do not put secrets in docs.
3. Keep a publicly understandable redirect/deprecation period from the legacy address **only if ORCID permits that transitional use**. Avoid leaking personal team data in URL redirects.
4. Consider a GitHub repository rename (GitHub may redirect old links) only after changing citations and pinned URLs; verify actual redirects. Don't rename Python imports or CLI commands without compatibility aliases and a documented deprecation cycle.
5. Regenerate icons and all video title cards. Label the project “Independent; not an official ORCID service”. Apply trademark attribution to landing pages using ORCID-specific subdomains.
6. Verify the built client, docs, service worker, CI, authentication, public API calls, and static widgets end to end on the new URL.
7. Announce the new canonical URLs only when deployed and checked. Do not imply permission via a disclaimer alone.

**No rename, DNS, OAuth, or Firebase project changes are performed by this document.**
