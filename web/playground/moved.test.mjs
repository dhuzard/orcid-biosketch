import { test } from 'node:test';
import assert from 'node:assert/strict';
import { forwardUrl, isLegacyHost, NEW_ORIGIN } from './moved.js';

test('only the old addresses are treated as legacy', () => {
  assert.ok(isLegacyHost('orcid-playground-889.web.app'));
  assert.ok(isLegacyHost('orcid-playground-889.firebaseapp.com'));
  assert.ok(!isLegacyHost('science-record-player.web.app'));
  assert.ok(!isLegacyHost('orcid-playground-889.web.app.evil.example'));
});
test('forwarding keeps path, query and fragment on the new host only', () => {
  assert.equal(forwardUrl({ pathname: '/network/', search: '?sample=1', hash: '#groups' }), 'https://science-record-player.web.app/network/?sample=1#groups');
  assert.equal(new URL(forwardUrl({ pathname: '//evil.example/', search: '', hash: '' })).origin, NEW_ORIGIN);
});
