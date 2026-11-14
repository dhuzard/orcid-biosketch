// Browser checks for the dual-path homepage (issue #53), run by tests/test_homepage.py.
// Usage: node tests/e2e/homepage.e2e.cjs http://127.0.0.1:PORT
// Exit 0 = pass, 1 = a check failed, 77 = no usable browser (the pytest wrapper skips).
const assert = require('node:assert/strict');

let chromium;
try { ({ chromium } = require('playwright')); } catch { process.exit(77); }
const BASE = process.argv[2].replace(/\/$/, '');

// The Python engine (Pyodide) and every ORCID host are blocked: the homepage must be
// usable and must not read any record before the visitor asks for one.
async function open(browser, viewport, path = '/', setup) {
  const page = await browser.newPage({ viewport, serviceWorkers: 'block' });
  page.setDefaultTimeout(15000);
  const external = [];
  await page.route('**/*', route => {
    const url = new URL(route.request().url());
    if (!url.href.startsWith(BASE)) { external.push(url.href); return route.abort(); }
    if (url.pathname.startsWith('/pyodide/')) return route.abort();
    return route.continue();
  });
  if (setup) await setup(page);
  await page.goto(BASE + path);
  await page.waitForLoadState('networkidle');
  return { page, external };
}

const box = (page, selector) => page.locator(selector).first().evaluate(e => {
  const r = e.getBoundingClientRect();
  return { top: r.top, bottom: r.bottom, left: r.left, right: r.right, height: r.height, visible: r.width > 0 && r.height > 0 };
});
const noHorizontalScroll = page => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);

async function focusOrder(page, steps = 40) {
  await page.evaluate(() => document.activeElement?.blur());
  const order = [];
  for (let i = 0; i < steps; i += 1) {
    await page.keyboard.press('Tab');
    order.push(await page.evaluate(() => {
      const e = document.activeElement;
      if (e.closest('.hero') && e.matches('a[href="/feedback/"]')) return 'hero-feedback';
      return e.id || e.dataset.trackCta || (e.hasAttribute('data-sample') ? 'sample-profile' : '') || e.dataset.orcid
        || e.getAttribute('href') || e.textContent.trim();
    }));
  }
  return order;
}

const checks = {
  async desktopLayouts(browser) {
    for (const viewport of [{ width: 1280, height: 800 }, { width: 1366, height: 768 }, { width: 1920, height: 1080 }]) {
      const { page } = await open(browser, viewport);
      const a = await box(page, '#track-explore-title');
      const b = await box(page, '#track-connect-title');
      // Side by side, at the same height: equal prominence.
      assert.equal(Math.round(a.top), Math.round(b.top), `${viewport.width}: track headings level`);
      assert.ok(a.right <= b.left, `${viewport.width}: tracks side by side`);
      // Both first actions are visible without scrolling.
      for (const cta of ['#lookup button[type=submit]', '[data-track-cta=connect]', '[data-track-cta=sample]', '[data-sample]']) {
        const r = await box(page, cta);
        assert.ok(r.visible && r.bottom <= viewport.height, `${viewport.width}x${viewport.height}: ${cta} above the fold (bottom ${r.bottom})`);
      }
      assert.equal((await box(page, '.paths')).visible, false, 'path chooser is only for small screens');
      assert.ok(await noHorizontalScroll(page));
      await page.close();
    }
  },

  async mobileLayouts(browser) {
    for (const viewport of [{ width: 320, height: 568 }, { width: 375, height: 667 }]) {
      const { page } = await open(browser, viewport);
      assert.ok(await noHorizontalScroll(page), `${viewport.width}: no horizontal scroll`);
      const h1 = await box(page, 'h1');
      const links = page.locator('.paths a');
      assert.equal(await links.count(), 2);
      const [explore, connect] = [await box(page, '.paths a >> nth=0'), await box(page, '.paths a >> nth=1')];
      // Both paths on the first screen, side by side and equally sized, right below the headline.
      // A 24px margin absorbs font-metric differences between machines (CI fonts render taller).
      for (const r of [explore, connect]) assert.ok(r.visible && r.bottom <= viewport.height - 24, `${viewport.width}: path visible on first screen with margin (bottom ${r.bottom})`);
      assert.equal(Math.round(explore.top), Math.round(connect.top));
      assert.equal(Math.round(explore.height), Math.round(connect.height));
      assert.ok(explore.top >= h1.bottom && explore.top - h1.bottom < 40, `${viewport.width}: chooser follows the headline`);
      // Tracks stack: A, then B.
      const a = await box(page, '#track-explore'); const b = await box(page, '#track-connect');
      assert.ok(b.top > a.bottom);
      assert.ok(a.right <= viewport.width && b.right <= viewport.width);
      // The chooser jumps to the track.
      await links.nth(1).click();
      await page.waitForFunction(() => location.hash === '#track-connect');
      await page.waitForFunction(() => { const r = document.querySelector('#track-connect-title').getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight; });
      await page.close();
    }
  },

  async keyboardFocusOrder(browser) {
    const { page } = await open(browser, { width: 1280, height: 800 });
    const order = await focusOrder(page);
    assert.equal(order[0], '#main', 'skip link comes first');
    const at = key => { const i = order.indexOf(key); assert.ok(i >= 0, `${key} reachable by Tab: ${order.join(' | ')}`); return i; };
    const sequence = ['orcid', 'Explore', 'sample-profile', '0000-0002-1825-0097', 'connect', 'sample', 'hero-feedback'].map(at);
    assert.deepEqual([...sequence].sort((x, y) => x - y), sequence, `track A, then track B: ${order.join(' | ')}`);
    assert.ok(!order.includes('#track-explore'), 'hidden chooser is not focusable on desktop');
    // The CTA is a real link that keyboard users can activate.
    await page.locator('[data-track-cta=connect]').focus();
    await Promise.all([page.waitForURL(`${BASE}/network/#contacts`), page.keyboard.press('Enter')]);
    await page.close();

    const mobile = await open(browser, { width: 375, height: 667 });
    const small = await focusOrder(mobile.page);
    const [paths, input] = [small.indexOf('#track-explore'), small.indexOf('orcid')];
    assert.ok(paths >= 0 && small.indexOf('#track-connect') === paths + 1 && paths < input, `mobile: chooser before the tracks: ${small.join(' | ')}`);
    await mobile.page.close();
  },

  async ctaTargetsAndConsent(browser) {
    // Track B, plain: opens the browser-local network, with no prompt and no import.
    const { page, external } = await open(browser, { width: 1280, height: 800 });
    let dialogs = 0;
    page.on('dialog', d => { dialogs += 1; d.dismiss(); });
    await Promise.all([page.waitForURL(`${BASE}/network/#contacts`), page.click('[data-track-cta=connect]')]);
    await page.waitForLoadState('networkidle');
    assert.equal(dialogs, 0);
    assert.deepEqual(external, [], 'no request leaves the site');

    // Track B, sample: nothing is added until the visitor confirms the labelled sample.
    await page.goto(BASE + '/');
    page.removeAllListeners('dialog');
    const asked = new Promise(resolve => page.once('dialog', d => { resolve(d.message()); d.dismiss(); }));
    await page.click('[data-track-cta=sample]');
    const message = await asked;
    assert.match(message, /labelled sample/);
    assert.match(message, /stored in this browser/);
    await page.waitForURL(`${BASE}/network/#groups`);
    await page.close();
  },

  async noReadBeforeConfirmation(browser) {
    // A link carrying an iD fills the form but waits for the visitor to press Explore.
    const { page, external } = await open(browser, { width: 375, height: 667 }, '/?orcid=0000-0002-1825-0097');
    await page.waitForFunction(() => document.querySelector('#status').textContent.includes('Press Explore'));
    assert.equal(await page.inputValue('#orcid'), '0000-0002-1825-0097');
    assert.deepEqual(external, []);
    assert.equal(await page.locator('#result').isHidden(), true);
    await page.close();
  },

  async emptyLoadingAndErrorStates(browser) {
    // Empty: submitting nothing explains what to enter, and reads nothing.
    const { page, external } = await open(browser, { width: 320, height: 568 });
    assert.equal(await page.textContent('#status'), '', 'quiet status before any action');
    assert.equal(await page.getAttribute('#status', 'role'), 'status');
    await page.click('#lookup button[type=submit]');
    await page.waitForSelector('#status.error');
    assert.match(await page.textContent('#status'), /Enter an ORCID iD/);
    assert.equal(await page.locator('#result').isHidden(), true);
    assert.deepEqual(external, []);

    await page.close();

    // Loading: while the engine starts, the stored profile shows progress and disables the buttons.
    const slow = await open(browser, { width: 375, height: 667 }, '/', p => p.route('**/engine.js', () => { /* never answers */ }));
    await slow.page.click('[data-sample]');
    await slow.page.waitForFunction(() => document.querySelector('#status').textContent.includes('Loading the stored sample profile'));
    assert.equal(await slow.page.locator('#status .bar').count(), 1);
    assert.equal(await slow.page.isDisabled('[data-sample]'), true);
    assert.equal(await slow.page.isDisabled('#lookup button[type=submit]'), true);
    assert.deepEqual(slow.external, [], 'the stored profile is read from this site, not ORCID');
    await slow.page.close();

    // Engine unavailable (here: runtime blocked): a plain error, and the buttons come back.
    const offline = await open(browser, { width: 1280, height: 800 });
    await offline.page.click('[data-sample]');
    await offline.page.waitForSelector('#status.error');
    assert.match(await offline.page.textContent('#status'), /engine could not start/);
    assert.equal(await offline.page.isDisabled('[data-sample]'), false);
    await offline.page.close();

    // Error: a missing stored profile is reported, not silently ignored.
    const broken = await open(browser, { width: 1280, height: 800 }, '/', p => p.route('**/generated/biosketch.json', r => r.fulfill({ status: 404, body: '' })));
    await broken.page.click('[data-sample]');
    await broken.page.waitForSelector('#status.error');
    assert.match(await broken.page.textContent('#status'), /Could not load the stored sample \(HTTP 404\)/);
    await broken.page.close();
  },
};

(async () => {
  let browser;
  try { browser = await chromium.launch(); } catch (error) { console.error(error.message); process.exit(77); }
  let failed = 0;
  for (const [name, check] of Object.entries(checks)) {
    try { await check(browser); console.log(`ok - ${name}`); } catch (error) { failed += 1; console.log(`not ok - ${name}\n${error.stack}`); }
  }
  await browser.close();
  process.exit(failed ? 1 : 0);
})();
