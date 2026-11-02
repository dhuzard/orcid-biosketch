// Compose an end-to-end scientist-facing feature tour from verified screen takes.
// Usage: node demo/full-tour.mjs site
// Requires render.mjs, groups.mjs, contacts.mjs and extras.mjs outputs.
import { chromium } from 'playwright';
import { execFileSync } from 'node:child_process';
import { existsSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { OUT, RAW, SITE, cut, concat, titleCard, square } from './lib.mjs';

const duration = file => Number(execFileSync('ffprobe',
  ['-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',file],
  { encoding: 'utf8' }).trim());
const required = ['orcid-playground-full-demo.mp4', 'groups-full-demo.mp4',
  'contacts-full-demo.mp4', 'extras-privacy-and-feedback.mp4'];
for (const name of required) if (!existsSync(resolve(OUT, name))) {
  throw new Error('Missing ' + name + '; render the four separate demo scripts first.');
}
const browser = await chromium.launch();
try {
  const intro = await titleCard(browser, 'tour-intro',
    `<h1>Your public research record,<br><em>put to work.</em></h1><p>Explore a scientist-first, open-source toolkit based on ORCID record assertions.</p><div><span class="pill">Profiles and exports</span><span class="pill">Contacts and groups</span></div>`, 5);
  const outro = await titleCard(browser, 'tour-outro',
    `<h1>Try it. Question it.<br><em>Help shape it.</em></h1><p>Independent of ORCID, Inc. No account needed to explore public records.</p><div><span class="pill">https://${SITE}/</span><span class="pill">/feedback/</span></div>`, 7);
  // Long cuts have their own opening and closing title cards; trim them so the tour feels continuous.
  const specs = [
    {file:required[0],from:5.5,tail:5.1,title:'Studio and research network'},
    {file:required[2],from:5.5,tail:5.2,title:'Contacts and conference follow-ups'},
    {file:required[1],from:5.8,tail:5.2,title:'Working groups and evidence-based visuals'},
    {file:required[3],from:0,tail:0,title:'Browser backups, encrypted packages and feedback'},
  ];
  let start = duration(intro);
  const chapters = [{time:0,title:'Introduction'}];
  const segments = [intro];
  for (const [i,s] of specs.entries()) {
    const input = resolve(OUT,s.file);
    const length = duration(input);
    if (length <= s.from + s.tail + 1) throw new Error('Unexpectedly short video: ' + s.file);
    const part = cut(input, s.from, length-s.tail, resolve(RAW,`full-chapter-${i}.mp4`));
    chapters.push({time:start,title:s.title});
    start += duration(part);
    segments.push(part);
  }
  chapters.push({time:start,title:'Try it and share feedback'});
  segments.push(outro);
  const output = resolve(OUT,'researcher-complete-tour.mp4');
  concat(segments, output);
  // A short native-video-friendly teaser (opening + direct CTA, both accurate for the hosted version).
  const trailer = resolve(OUT, 'scientist-invitation-short.mp4');
  const teaser = cut(resolve(OUT,required[0]),5.5,23,resolve(RAW,'teaser-studio.mp4'));
  const privateTools = cut(resolve(OUT,required[3]),0,14,resolve(RAW,'teaser-local.mp4'));
  concat([intro,teaser,privateTools,outro],trailer);
  square(trailer,resolve(OUT,'scientist-invitation-square.mp4'));
  // Human-reviewable chapter listing and text synopsis; NOT a fake verbatim narration transcript.
  const stamp = seconds => {
    const n=Math.floor(seconds), hh=Math.floor(n/3600),mm=Math.floor(n/60)%60,ss=n%60;
    return [hh,mm,ss].map(x=>String(x).padStart(2,'0')).join(':');
  };
  writeFileSync(resolve(OUT,'chapters.txt'),chapters.map(x=>`${stamp(x.time)} ${x.title}`).join('\n')+'\n');
  writeFileSync(resolve(OUT,'video-review-checklist.txt'),
    'Source: filmed application UI in a local build.\n' +
    'Group records: fictional, clearly marked Demo; shared DOI assertions are not confirmed collaboration.\n' +
    'Cloud Teams and personal account sync are excluded pending verified activation.\n' +
    'Funders: exported biosketches are drafts only.\n' +
    'Videos are silent, with on-screen captions; no spoken narration or verbatim subtitles are claimed.\n' +
    'Publication is held pending review of ORCID branding and the actual hosted feature set.\n');
  console.log('Rendered',output,'duration',duration(output),'sec');
} finally { await browser.close(); }
