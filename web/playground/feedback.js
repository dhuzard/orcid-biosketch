// The mailto workflow is deliberately client-only: no form POST, no analytics,
// no access to the research-network workspace, and no claims of successful delivery.
export const RECIPIENT = 'neuronautix@gmail.com';
const safe = value => String(value || '').trim();
export function composeFeedback({ role, area, task, observed, improvement }) {
  const chosen = safe(area);
  const intended = safe(task);
  const actual = safe(observed);
  if (!chosen || !intended || !actual) throw new Error('Select a feature and describe your task and observation.');
  const message = [
    'ORCID Playground — scientist feedback',
    '',
    'Research context: ' + (safe(role) || 'Not specified'),
    'Feature: ' + chosen,
    '',
    'Task:',
    intended,
    '',
    'Expected / observed:',
    actual,
    '',
    'Requested improvement:',
    safe(improvement) || 'Not specified',
    '',
    'Please do not include sensitive or private research data.',
  ].join('\n');
  // A reasonably short mailto URI works more reliably across mobile mail apps.
  return { message, mailto: 'mailto:' + RECIPIENT + '?subject=' + encodeURIComponent('ORCID Playground — scientist feedback') + '&body=' + encodeURIComponent(message) };
}
function setup() {
  const form = document.querySelector('#feedback-form');
  const status = document.querySelector('#feedback-status');
  const values = () => Object.fromEntries(new FormData(form));
  const announce = message => { status.textContent = message; };
  form.addEventListener('submit', event => {
    event.preventDefault();
    try {
      const output = composeFeedback(values());
      // Opening an email composer does NOT mean feedback has been sent.
      announce('Email draft prepared. Review it and press Send in your email application.');
      window.location.href = output.mailto;
    } catch (error) { announce(error.message); }
  });
  document.querySelector('#copy-feedback').addEventListener('click', async () => {
    try {
      const output = composeFeedback(values());
      await navigator.clipboard.writeText(output.message);
      announce('Copied. Paste the text into an email or another feedback channel.');
    } catch (error) { announce(error.message || 'Could not copy. Try the email draft button.'); }
  });
}
if (typeof document !== 'undefined') setup();
