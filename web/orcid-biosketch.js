class OrcidBiosketch extends HTMLElement {
  async connectedCallback() {
    const src = this.getAttribute("src");
    if (!src) return this.renderError("Missing src attribute");
    this.innerHTML = "<p>Loading biosketch…</p>";
    try {
      const response = await fetch(src);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const bio = await response.json();
      const p = bio.person;
      const limit = Number(this.getAttribute("works") || 5);
      const works = bio.works.slice(0, limit).map(w => {
        const doi = w.identifiers && w.identifiers.doi;
        const href = doi ? `https://doi.org/${doi}` : w.url;
        const title = href ? `<a href="${this.escape(href)}">${this.escape(w.title)}</a>` : this.escape(w.title);
        return `<li>${title} (${this.escape((w.publication_date || "").slice(0, 4))})</li>`;
      }).join("");
      this.innerHTML = `<article class="orcid-biosketch"><h2>${this.escape(p.name)}</h2>
        <p><a href="${this.escape(p.orcid_url)}">ORCID ${this.escape(p.orcid)}</a></p>
        <p>${this.escape(p.biography)}</p>${works ? `<h3>Selected works</h3><ul>${works}</ul>` : ""}</article>`;
    } catch (error) { this.renderError(`Could not load biosketch: ${error.message}`); }
  }
  escape(value) {
    const node = document.createElement("div"); node.textContent = value || ""; return node.innerHTML;
  }
  renderError(message) { this.innerHTML = `<p role="alert">${this.escape(message)}</p>`; }
}
customElements.define("orcid-biosketch", OrcidBiosketch);

