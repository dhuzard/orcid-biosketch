// The app moved from orcid-playground-889.web.app to science-record-player.web.app (BACKLOG INF-13).
// Both addresses serve this same build. On the old one, visitors with nothing saved there are
// forwarded at once (path, query and #fragment kept). Browser storage belongs to an address, so
// anyone who has a research network saved on the old one is shown how to carry it over first.
export const NEW_ORIGIN = 'https://science-record-player.web.app';
export const LEGACY_HOSTS = ['orcid-playground-889.web.app', 'orcid-playground-889.firebaseapp.com'];

export const isLegacyHost = hostname => LEGACY_HOSTS.includes(hostname);
export const forwardUrl = ({ pathname, search, hash }) => NEW_ORIGIN + pathname + search + hash;

async function hasLocalData() {
  try {
    if (localStorage.getItem('orcid-playground-last-visit')) return true;
  } catch { /* storage blocked: fall through */ }
  try {
    if (indexedDB.databases) return (await indexedDB.databases()).length > 0;
  } catch { /* unsupported */ }
  return false;
}

function banner() {
  const note = document.createElement('div');
  note.setAttribute('role', 'alert');
  Object.assign(note.style, { background: '#3a2737', color: '#fff', padding: '12px 16px', font: '15px/1.5 system-ui,sans-serif', position: 'relative', zIndex: '20' });
  const link = (href, text) => { const a = document.createElement('a'); a.href = href; a.textContent = text; a.style.color = '#e2b4c0'; a.style.fontWeight = '700'; return a; };
  note.append('This tool has moved to ', link(forwardUrl(location), 'science-record-player.web.app'),
    '. Your research network is saved in this browser for this old address only. Open ',
    link('/network/', 'Research network'), ', choose “Download my workspace”, then use “Restore from file” on the new site.');
  document.body.prepend(note);
}

export async function checkMoved(loc = location) {
  if (!isLegacyHost(loc.hostname)) return 'current';
  if (await hasLocalData()) {
    if (document.body) banner(); else addEventListener('DOMContentLoaded', banner);
    return 'banner';
  }
  loc.replace(forwardUrl(loc));
  return 'forwarded';
}

if (typeof location !== 'undefined' && typeof document !== 'undefined') checkMoved();
