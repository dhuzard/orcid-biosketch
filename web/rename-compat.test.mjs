// The widgets were renamed <srp-biosketch> / <srp-group> (BACKLOG INF-14); the old tags and
// files stay as deprecated aliases so existing embeds keep working.
import assert from "node:assert/strict";
import test from "node:test";

const defined = new Map();
globalThis.document = { baseURI: "https://lab.example/", createElement: () => ({ content: { cloneNode: () => ({}) } }) };
globalThis.HTMLElement = class {};
globalThis.customElements = { get: name => defined.get(name), define: (name, cls) => { assert.ok(!defined.has(name)); defined.set(name, cls); } };

test("new and deprecated tags are both registered, each with its own class", async () => {
  await import("./srp-biosketch.js");
  await import("./srp-group.js");
  for (const [name, old] of [["srp-biosketch", "orcid-biosketch"], ["srp-group", "orcid-group"]]) {
    assert.ok(defined.get(name) && defined.get(old), name);
    assert.notEqual(defined.get(name), defined.get(old));
    assert.ok(defined.get(old).prototype instanceof defined.get(name));
  }
});

test("the deprecated files re-export the new modules", async () => {
  const oldGroup = await import("./orcid-group.js"), newGroup = await import("./srp-group.js");
  assert.equal(oldGroup.validSnapshot, newGroup.validSnapshot);
  const oldBio = await import("./orcid-biosketch.js"), newBio = await import("./srp-biosketch.js");
  assert.equal(oldBio.safeHttpUrl, newBio.safeHttpUrl);
});
