import test from 'node:test';
import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { protocolSuite } from './protocol-suite.mjs';
import { startMySQLFixture } from './mysql-fixture.mjs';
import { snapshotFromSQL } from '../scripts/export-sqlite.mjs';
import { importSnapshot } from '../scripts/import-snapshot.mjs';
import { readFile } from 'node:fs/promises';

protocolSuite(startMySQLFixture);

test('MySQL concurrent rate limits allocate each count once and expiry cleanup works', async () => {
  const fixture = await startMySQLFixture();
  try {
    const counts = await Promise.all(Array.from({ length: 24 }, () => fixture.STORE.incrementLimit('concurrent', 100)));
    assert.deepEqual(counts.sort((a, b) => a - b), Array.from({ length: 24 }, (_, i) => i + 1));
    await fixture.STORE.cleanup(101);
    assert.equal(await fixture.STORE.incrementLimit('concurrent', 200), 1);
  } finally { await fixture.close(); }
});

test('MySQL preserves Unicode nicknames and authentication hashes across connections', async () => {
  const fixture = await startMySQLFixture();
  try {
    const id = randomUUID(), now = new Date().toISOString();
    await fixture.STORE.createUser(id, '训练者 🐈', 'a'.repeat(64), now);
    await fixture.STORE.createUser(id, 'replacement', 'b'.repeat(64), now);
    const user = await fixture.STORE.findUser(id);
    assert.equal(user.nickname, '训练者 🐈');
    assert.equal(user.token_hash, 'a'.repeat(64));
    assert.equal(user.created_at, now);
  } finally { await fixture.close(); }
});

test('Snapshot migration preserves identities and records; refuses overwrite and rolls back invalid data', async () => {
  const fixture = await startMySQLFixture();
  try {
    const schema = await readFile(new URL('./schema.sql', import.meta.url), 'utf8');
    const id = randomUUID(), timestamp = '2026-10-08T10:00:00.000Z';
    const sql = schema + `\nINSERT INTO users VALUES('${id}','训练者 🐈','${'a'.repeat(64)}','${timestamp}','${timestamp}');
      INSERT INTO ac_events VALUES('${id}','${'b'.repeat(64)}','${'c'.repeat(64)}','${timestamp}','2026-10-08',1500,'${timestamp}');`;
    const snapshot = snapshotFromSQL(sql);
    const invalid = structuredClone(snapshot);
    invalid.events.push({ ...invalid.events[0], problem_key: 'd'.repeat(64) });
    await assert.rejects(() => importSnapshot(fixture.STORE, invalid));
    assert.equal(await fixture.STORE.findUser(id), null);
    assert.equal(await fixture.countEvents(), 0);
    assert.deepEqual(await importSnapshot(fixture.STORE, snapshot), { users: 1, events: 1 });
    assert.equal((await fixture.STORE.findUser(id)).token_hash, 'a'.repeat(64));
    assert.equal((await fixture.STORE.rankings(id, null)).own.count, 1);
    await assert.rejects(() => importSnapshot(fixture.STORE, snapshot), /Destination must be empty/);
    assert.equal(await fixture.countEvents(), 1);
  } finally { await fixture.close(); }
});
