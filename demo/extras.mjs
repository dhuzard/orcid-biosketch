// Additional real UI footage: browser backup/restore, encrypted group package,
// in-app scientist feedback. Uses only the application's labelled sample workspace.
import { chromium } from 'playwright';
import { resolve } from 'node:path';
import { readFileSync } from 'node:fs';
import { OUT, RAW, caption, record, cut, square, serveSite } from './lib.mjs';

const site = await serveSite();
const browser = await chromium.launch();
try {
  let begin = 0, finish = 0;
  const capture = await record(browser, 'extra-take', async (page, now) => {
    // Log every dialog: an export failure surfaces as an alert, which would otherwise be accepted silently.
    page.on('dialog', dialog => { console.log(`dialog (${dialog.type()}): ${dialog.message().split('\n')[0]}`); dialog.accept(); });
    page.on('pageerror', error => console.log('page error:', error.message));
    page.on('console', message => { if (message.type() === 'error') console.log('console error:', message.text()); });
    await page.goto(site.base + 'network/');
    await page.waitForSelector('#demo');
    await page.waitForTimeout(10000);
    await page.click('#demo');
    // Wait for the in-browser engine to finish loading the sample workspace before exporting it.
    await page.waitForSelector('#demo-banner:not([hidden])', { timeout: 120000 });
    await page.waitForTimeout(1100);
    begin = now();
    await caption(page, 'BROWSER-LOCAL', 'Keep your working notes on your device.',
      'Download a backup of the browser workspace. It can include private notes; share carefully.');
    await page.waitForTimeout(3300);
    const [backup] = await Promise.all([
      page.waitForEvent('download', { timeout: 90000 }),
      page.locator('#export-workspace').click(),
    ]);
    const bytes = readFileSync(await backup.path());
    await page.waitForTimeout(1700);
    await caption(page, 'RESTORE', 'Make a validated restore.',
      'A backup can replace the local workspace after you review and confirm its contents.');
    await page.locator('#import-workspace-file').setInputFiles({
      name: 'demo-browser-workspace.json', mimeType: 'application/json', buffer: bytes,
    });
    await page.waitForTimeout(3200);

    await page.goto(site.base + 'group/?packages=1');
    await page.waitForSelector('#packages-details');
    await page.locator('#packages-details').evaluate(el => { el.open = true; });
    await page.waitForSelector('#pack-group option', { state: 'attached', timeout: 90000 });
    await page.waitForTimeout(1300);
    await caption(page, 'ENCRYPTED TEAM PACKAGE', 'Share a curated group deliberately.',
      'Encryption happens in this browser. The file contains local group details and needs a separate password.');
    await page.locator('#pack-password').fill('Video-Demo-Passphrase-2026');
    await page.locator('#pack-password-again').fill('Video-Demo-Passphrase-2026');
    const [encrypted] = await Promise.all([
      page.waitForEvent('download', { timeout: 35000 }),
      page.locator('#pack-export button[type=submit]').click(),
    ]);
    await page.waitForTimeout(1700);
    await caption(page, 'DECRYPT & PREVIEW', 'A file is not consent.',
      'Anyone holding both the file and password can read it. Group membership is still unconfirmed.');
    await page.locator('#pack-file').setInputFiles({
      name: 'demo-team-package.json', mimeType: 'application/json',
      buffer: readFileSync(await encrypted.path()),
    });
    await page.locator('#pack-open-password').fill('Video-Demo-Passphrase-2026');
    await page.locator('#pack-import button[type=submit]').click();
    await page.waitForSelector('#pack-preview button', { timeout: 25000 });
    await page.waitForTimeout(2500);

    await page.goto(site.base + 'feedback/');
    await page.waitForSelector('#feedback-form');
    await caption(page, 'YOUR RESEARCH WORKFLOWS', 'Suggest a feature without GitHub.',
      'Tell us what you tried, what was confusing and what would make this useful. Nothing is sent automatically.');
    await page.locator('#role').selectOption('Researcher');
    await page.locator('#area').selectOption('Studio / Record check / exports');
    await page.locator('#task').fill('Prepare a reusable bibliography for a grant proposal.');
    await page.locator('#observed').fill('I would like clearer information about missing DOIs.');
    await page.locator('#improvement').fill('Provide a report listing publications without DOIs.');
    await page.waitForTimeout(3800);
    // Deliberately do NOT submit email. A video recording must not email the maintainer.
    await caption(page, 'TRY IT. QUESTION IT.', 'Make the next version better.',
      'Independent open source. ORCID records contain assertions, not independently verified credentials.');
    await page.waitForTimeout(4200);
    finish = now();
  });
  // Trim precisely to real UI activity, not a fixed initialization delay.
  const trimmed = cut(capture, begin + 0.05, finish - 0.05, resolve(RAW, 'extra-all.mp4'));
  const out = resolve(OUT, 'extras-privacy-and-feedback.mp4');
  const { copyFileSync } = await import('node:fs');
  copyFileSync(trimmed, out);
  square(out, resolve(OUT, 'extras-clip-privacy-and-feedback.mp4'));
  console.log('Created', out);
} finally {
  await browser.close();
  site.stop();
}
