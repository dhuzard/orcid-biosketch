// A shareable group link must carry only a group name and public ORCID iDs, in
// the URL fragment, so local roles, notes and selections can never leak via a link.
import test from 'node:test';
import assert from 'node:assert/strict';
import { decodeGroup, encodeGroup } from './group-link.js';

const IDS = ['0000-0002-1825-0097', '0000-0003-4820-7951'];

test('a group link is a fragment holding only a name and public iDs', () => {
  const hash = encodeGroup({ name: 'Demo lab', members: IDS, roles: { x: 'PI' }, notes: 'private note', requests: ['r'] });
  assert.ok(hash.startsWith('#'), 'the group lives in the fragment, which browsers do not send to the server');
  const raw = JSON.parse(Buffer.from(hash.slice(4).replace(/-/g, '+').replace(/_/g, '/'), 'base64').toString('utf8'));
  assert.deepEqual(Object.keys(raw).sort(), ['m', 'n']);
  assert.doesNotMatch(JSON.stringify(raw), /private note|PI/);
  assert.deepEqual(decodeGroup(hash), { name: 'Demo lab', members: IDS });
});

test('decoding drops anything that is not a valid public iD', () => {
  const forged = '#v1.' + Buffer.from(JSON.stringify({ n: 'X', m: [...IDS, '0000-0000-0000-0000', 42], notes: 'x' })).toString('base64url');
  assert.deepEqual(decodeGroup(forged), { name: 'X', members: IDS });
});
