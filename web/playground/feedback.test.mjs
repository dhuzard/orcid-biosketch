import { test } from 'node:test';
import assert from 'node:assert/strict';
import { composeFeedback, RECIPIENT } from './feedback.js';

test('feedback requires scientific task, observation and feature', () => {
  for (const missing of ['area', 'task', 'observed']) {
    const values = { area: 'Studio', task: 'Export bibliography', observed: 'Missing DOI' };
    values[missing] = '';
    assert.throws(() => composeFeedback(values), /Select a feature/);
  }
});
test('mailto draft includes user-entered task but no browser workspace', () => {
  const output = composeFeedback({ role: 'Researcher', area: 'Studio', task: 'Export works', observed: 'No DOI',
    improvement: 'Report identifiers that could not be exported' });
  assert.ok(output.mailto.startsWith('mailto:' + RECIPIENT));
  assert.match(decodeURIComponent(output.mailto), /Export works/);
  assert.match(output.message, /Report identifiers/);
  assert.doesNotMatch(output.message, /localStorage|IndexedDB/);
});
