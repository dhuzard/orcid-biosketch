import assert from "node:assert/strict";
import test from "node:test";

globalThis.document = {
  baseURI: "https://example.org/profile/",
  createElement() {
    return {content: {cloneNode() { return {}; }}, innerHTML: ""};
  },
};
globalThis.HTMLElement = class {};
globalThis.customElements = {get() { return true; }, define() {}};

const {safeHttpUrl} = await import("./orcid-biosketch.js");

test("safeHttpUrl allows only browser-safe web links", () => {
  assert.equal(safeHttpUrl("https://orcid.org/0000-0002-1825-0097"),
               "https://orcid.org/0000-0002-1825-0097");
  assert.equal(safeHttpUrl("/paper"), "https://example.org/paper");
  assert.equal(safeHttpUrl("javascript:alert(1)"), "");
  assert.equal(safeHttpUrl("data:text/html,unsafe"), "");
  assert.equal(safeHttpUrl("not a valid URL", "not a base"), "");
});
