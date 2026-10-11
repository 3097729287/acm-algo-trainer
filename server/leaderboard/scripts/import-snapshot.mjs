import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { openStore } from '../src/mysql-store.mjs';

export async function importSnapshot(store, snapshot) {
  if (snapshot?.format !== 'tb-ranking-v1' || !Array.isArray(snapshot.users) || !Array.isArray(snapshot.events)) {
    throw new Error('Unsupported migration format');
  }
  return store.transaction(async connection => {
    // Run with the API stopped. Range locks also block concurrent registration
    // and event writes while importing into the empty destination.
    const [users] = await connection.query('SELECT user_id FROM users FOR UPDATE');
    const [events] = await connection.query('SELECT user_id FROM ac_events FOR UPDATE');
    if (users.length || events.length) throw new Error('Destination must be empty');
    for (const user of snapshot.users) {
      await connection.execute('INSERT INTO users(user_id,nickname,token_hash,created_at,updated_at) VALUES(?,?,?,?,?)',
        [user.user_id, user.nickname, user.token_hash, user.created_at, user.updated_at]);
    }
    for (const event of snapshot.events) {
      await connection.execute('INSERT INTO ac_events(user_id,problem_key,event_id,accepted_at,accepted_day,difficulty,received_at) VALUES(?,?,?,?,?,?,?)',
        [event.user_id, event.problem_key, event.event_id, event.accepted_at, event.accepted_day, event.difficulty, event.received_at]);
    }
    const [[userCount]] = await connection.query('SELECT COUNT(*) AS count FROM users');
    const [[eventCount]] = await connection.query('SELECT COUNT(*) AS count FROM ac_events');
    if (Number(userCount.count) !== snapshot.users.length || Number(eventCount.count) !== snapshot.events.length) {
      throw new Error('Migration count mismatch');
    }
    return { users: snapshot.users.length, events: snapshot.events.length };
  });
}

if (process.argv[1] && fileURLToPath(import.meta.url).toLowerCase() === resolve(process.argv[1]).toLowerCase()) {
  let store;
  try {
    if (!process.argv[2]) throw new Error('Migration file path is required');
    const snapshot = JSON.parse(await readFile(process.argv[2], 'utf8'));
    store = await openStore();
    process.stdout.write(JSON.stringify(await importSnapshot(store, snapshot)) + '\n');
  } catch {
    process.stderr.write('Migration failed and was rolled back; destination must be empty and source data valid\n');
    process.exitCode = 1;
  } finally { if (store) await store.close(); }
}
