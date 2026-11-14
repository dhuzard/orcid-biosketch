// Browser regression tests for the shared Science Record Player navigation (#54).
// Runs against a built site:  python scripts/build_site.py site && node --test web/navigation.browser.test.mjs
// SRP_SITE picks another build directory. Without Playwright or a built site the tests are
// skipped, unless SRP_REQUIRE_BROWSER=1 (CI), where a missing prerequisite is a failure.
import test from 'node:test';
import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { existsSync, readFileSync, statSync } from 'node:fs';
import { resolve, dirname, extname, join, normalize } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SITE = resolve(process.env.SRP_SITE || join(ROOT, 'site'));
const REQUIRED = process.env.SRP_REQUIRE_BROWSER === '1';

let chromium = null;
let reason = '';
// CommonJS resolution so NODE_PATH works (CI points it at demo/node_modules, which pins Playwright).
try { ({ chromium } = createRequire(import.meta.url)('playwright')); } catch { reason = 'playwright is not installed'; }
if (chromium && !existsSync(join(SITE, 'network', 'index.html'))) reason = `no built site at ${SITE}`;
if (reason && REQUIRED) throw new Error(`Browser navigation tests cannot run: ${reason}`);
const skip = reason ? `skipped: ${reason}` : false;

// The one information architecture, in order, on every page (#54).
const MENU = ['Explore', 'My Network', 'Public Group View', 'How it works', 'Feedback'];
const PAGES = { '/': 'Explore', '/network/': 'My Network', '/group/': 'Public Group View', '/feedback/': 'Feedback', '/team/': null };
// The documentation is built by Sphinx and bundled at /docs/ by the deploy workflow, not by build_site.py.
const BUILT_ELSEWHERE = new Set(['/docs/']);

const TYPES = { '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.ico': 'image/x-icon', '.wasm': 'application/wasm', '.zip': 'application/zip', '.webmanifest': 'application/manifest+json', '.md': 'text/markdown' };

function serve() {
  const server = createServer((req, res) => {
    const path = decodeURIComponent(new URL(req.url, 'http://x').pathname);
    let file = normalize(join(SITE, path));
    if (!file.startsWith(SITE)) { res.writeHead(403).end(); return; }
    if (existsSync(file) && statSync(file).isDirectory()) file = join(file, 'index.html');
    if (!existsSync(file)) { res.writeHead(404).end('not found'); return; }
    res.writeHead(200, { 'Content-Type': TYPES[extname(file)] || 'application/octet-stream' }).end(readFileSync(file));
  });
  return new Promise(ok => server.listen(0, '127.0.0.1', () => ok(server)));
}

let server, browser, base;
test.before(async () => {
  if (skip) return;
  server = await serve();
  base = `http://127.0.0.1:${server.address().port}`;
  browser = await chromium.launch();
});
test.after(async () => { await browser?.close(); server?.close(); });

// A fresh context per test: no service worker, no ORCID API calls leave the machine.
async function open(path, viewport = { width: 1280, height: 900 }) {
  const context = await browser.newContext({ viewport, serviceWorkers: 'block' });
  await context.route(url => !url.href.startsWith(base), route => route.abort());
  const page = await context.newPage();
  page.on('dialog', dialog => dialog.accept());
  await page.goto(base + path);
  return { page, close: () => context.close() };
}

const mainNav = page => page.locator('nav[aria-label="Main"]');
const labels = page => mainNav(page).locator('a .nav-label').allTextContents();

test('every page shows the same SRP brand and menu, with the current page marked', { skip }, async () => {
  for (const [path, current] of Object.entries(PAGES)) {
    const { page, close } = await open(path);
    await mainNav(page).waitFor();
    assert.deepEqual(await labels(page), MENU, path);
    const marked = await mainNav(page).locator('a[aria-current="page"] .nav-label').allTextContents();
    assert.deepEqual(marked, current ? [current] : [], path);
    // Cloud Teams are not activated in production: never offered from the menu.
    assert.equal(await mainNav(page).locator('a[href^="/team"]').count(), 0, path);
    const brand = page.locator('a.brand');
    assert.match(await brand.innerText(), /Science Record Player/, path);
    assert.match(await brand.innerText(), /Damien Huzard \/ Neuronautix/, path);
    // Brand and navigation chrome only (page body copy is audited separately, #55).
    const chrome = [await page.title(), ...await page.locator('header, aside, nav').allInnerTexts()].join('\n');
    for (const old of ['in good company', 'THE RESEARCH COMMONS', 'LOCAL PILOT', 'PILOT', 'Research network', 'Studio']) assert.ok(!chrome.includes(old), `${path} still shows "${old}"`);
    await close();
  }
});

test('the Teams page says it is experimental and unavailable, and points to local alternatives', { skip }, async () => {
  const { page, close } = await open('/team/');
  const note = page.locator('#teams-status');
  assert.match(await note.innerText(), /Experimental: private cloud Teams are not available yet/);
  assert.match(await page.title(), /experimental, not available/);
  assert.equal(await note.locator('a[href="/network/#groups"]').count(), 1);
  await close();
});

test('no dead links on public pages', { skip }, async () => {
  const seen = new Map();
  for (const path of Object.keys(PAGES)) {
    const { page, close } = await open(path);
    await mainNav(page).waitFor();
    for (const href of await page.locator('a[href]').evaluateAll(links => links.map(a => a.href))) {
      const url = new URL(href);
      if (url.origin !== base || BUILT_ELSEWHERE.has(url.pathname) || seen.has(url.pathname)) continue;
      seen.set(url.pathname, path);
    }
    await close();
  }
  for (const [pathname, from] of seen) {
    const res = await fetch(base + pathname);
    assert.equal(res.status, 200, `${pathname} (linked from ${from})`);
  }
  assert.ok(seen.has('/network/') && seen.has('/group/') && seen.has('/feedback/'));
});

test('menu works at 320px: no sideways scrolling, every item visible and large enough to tap', { skip }, async () => {
  for (const path of Object.keys(PAGES)) {
    const { page, close } = await open(path, { width: 320, height: 640 });
    await mainNav(page).waitFor();
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= 320), `${path} scrolls sideways at 320px`);
    for (const box of await mainNav(page).locator('a').evaluateAll(links => links.map(a => a.getBoundingClientRect().toJSON()))) {
      assert.ok(box.left >= 0 && box.right <= 320, `${path}: menu item off screen ${JSON.stringify(box)}`);
      assert.ok(box.height >= 40, `${path}: menu item too small to tap (${box.height}px)`);
    }
    await close();
  }
});

test('keyboard: skip link first, then the menu in order, with a visible focus ring', { skip }, async () => {
  for (const path of ['/', '/network/', '/group/']) {
    const { page, close } = await open(path);
    await mainNav(page).waitFor();
    await page.keyboard.press('Tab');
    assert.equal(await page.evaluate(() => document.activeElement.className), 'skip', path);
    const reached = [];
    for (let i = 0; i < 40 && reached.length < MENU.length; i++) {
      await page.keyboard.press('Tab');
      const info = await page.evaluate(() => {
        const a = document.activeElement;
        return a.closest('nav[aria-label="Main"]') ? { label: a.querySelector('.nav-label').textContent, outline: getComputedStyle(a).outlineStyle } : null;
      });
      if (info) { reached.push(info.label); assert.notEqual(info.outline, 'none', `${path}: ${info.label} has no focus ring`); }
    }
    assert.deepEqual(reached, MENU, path);
    await close();
  }
});

test('the skip link moves focus to the main content', { skip }, async () => {
  const { page, close } = await open('/group/');
  await page.keyboard.press('Tab');
  await page.keyboard.press('Enter');
  assert.equal(await page.evaluate(() => document.activeElement.id), 'main');
  await close();
});

test('My Network sections are a labelled navigation and existing deep links still select them', { skip }, async () => {
  for (const [hash, label, title] of [['#feed', 'Feed', 'The latest, together.'], ['#people', 'People', 'Follow your curiosity.'],
    ['#contacts', 'Contacts', 'Keep every conversation going.'], ['#groups', 'Groups', 'A shared place to work.'], ['#saved', 'Saved', 'Your next good read.']]) {
    const { page, close } = await open(`/network/${hash}`);
    const sections = page.getByRole('navigation', { name: /MY NETWORK/ });
    const current = sections.locator('a[aria-current="page"]');
    await current.waitFor({ timeout: 60000 });
    assert.match(await current.innerText(), new RegExp(label), hash);
    assert.equal(await page.locator('#title').innerText(), title, hash);
    assert.match(await page.title(), new RegExp(`^${label} · My Network · Science Record Player$`), hash);
    await close();
  }
});

test('the sample route still loads the labelled sample workspace on the Groups section', { skip }, async () => {
  const { page, close } = await open('/network/?sample=1#groups');
  await page.locator('#demo-banner:not([hidden])').waitFor({ timeout: 60000 });
  await page.locator('.group-card').first().waitFor();
  assert.match(await page.locator('.group-card').first().innerText(), /Local working group/i);
  assert.match(await page.getByRole('navigation', { name: /MY NETWORK/ }).locator('a[aria-current="page"]').innerText(), /Groups/);
  await close();
});

test('Public Group View routes still work: composer, shared #v1 link and ?packages=1', { skip }, async () => {
  let { page, close } = await open('/group/');
  await page.locator('#compose:not([hidden])').waitFor();
  await close();
  const link = '#v1.' + Buffer.from(JSON.stringify({ n: 'Navigation test group', m: ['0000-0002-1825-0097'] })).toString('base64url');
  ({ page, close } = await open(`/group/${link}`));
  await page.locator('#preview:not([hidden])').waitFor();
  assert.equal(await page.locator('#group-name').innerText(), 'Navigation test group');
  assert.match(await page.locator('#preview .disclosure').innerText(), /not confirmed by the people listed/);
  await close();
  ({ page, close } = await open('/group/?packages=1'));
  await page.waitForFunction(() => document.querySelector('#packages-details')?.open);
  await close();
});
