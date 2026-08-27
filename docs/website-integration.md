# Website integration guide

`orcid-biosketch` supports browser-time live synchronization and build-time static integration.

## Browser-time synchronization

The website loads the latest generated JSON whenever a visitor opens the page. No website rebuild is required after the biosketch repository synchronizes with ORCID.

```html
<script type="module" src="https://cdn.jsdelivr.net/gh/OWNER/orcid-biosketch@main/web/orcid-biosketch.js"></script>
<orcid-biosketch
  src="https://raw.githubusercontent.com/OWNER/orcid-biosketch/main/generated/biosketch.json"
  bio="true"
  works="all"
  search="true"
  pdf="true"
  provenance="true">
</orcid-biosketch>
```

Replace `OWNER` with the GitHub account containing the fork.

| Attribute | Values | Default | Purpose |
|---|---|---|---|
| `src` | URL | required | Published canonical JSON |
| `bio` | `true` / `false` | `true` | Approved biography |
| `works` | number / `all` | `10` | Maximum displayed outputs |
| `search` | `true` / `false` | `false` | Search, type filter and sorting |
| `pdf` | `true` / `false` | `false` | A4 print/PDF export |
| `provenance` | `true` / `false` | `true` | Source and update information |

The Shadow DOM prevents the component from overwriting host styles. Colors remain configurable:

```css
orcid-biosketch { --ob-accent:#005ea8; --ob-border:#d6dce2; --ob-bg:white; --ob-soft:#f5f7f9; --ob-muted:#52606d; }
```

## Build-time integration

Static generators can fetch `generated/biosketch.json` during a build. This improves indexing and works without browser JavaScript, but requires a website rebuild when data change.

### Astro

```astro
---
const response = await fetch('https://raw.githubusercontent.com/OWNER/orcid-biosketch/main/generated/biosketch.json');
const bio = await response.json();
---
<h1>{bio.person.name}</h1>
<p>{bio.person.biography}</p>
```

For browser-time synchronization, paste the generic component markup into an Astro page.

### Jekyll / GitHub Pages

Paste the browser-time markup into a page or layout. No Ruby plugin is required.

### Hugo

Add the markup to `layouts/shortcodes/orcid-biosketch.html`, then invoke the shortcode from content.

### Quarto / MyST

Use a raw HTML block for HTML websites. For PDF-native builds, include `generated/biosketch.md`, because browser components do not run in document PDF output.

## Scientist deployment checklist

1. Fork the repository.
2. Replace the example ORCID iD in `.github/workflows/sync.yml`.
3. Edit `config/biosketch.json` with approved overrides.
4. Run **Synchronize ORCID biosketch** in GitHub Actions.
5. Verify the generated JSON, JSON-LD and Markdown.
6. Insert the component markup into the scientist's website.
7. Update ORCID, rerun synchronization and confirm the website changes.

GitHub raw URLs suit personal sites and demonstrations. Production deployments may copy the JSON into the website's static assets during CI or publish it through institutional hosting. Cross-domain data endpoints must permit CORS.

## Security and privacy

- Only public ORCID data are retrieved.
- Remote values are rendered as text, not executed as HTML.
- Never expose ORCID access tokens in repositories or web pages.
- Overrides remain declared in provenance.
