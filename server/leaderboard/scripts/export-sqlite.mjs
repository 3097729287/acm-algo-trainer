import { DatabaseSync } from 'node:sqlite';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

export function snapshotFromSQL(sql) {
  const db = new DatabaseSync(':memory:');
  try {
    db.exec(sql);
    if (db.prepare('PRAGMA integrity_check').get().integrity_check !== 'ok' || db.prepare('PRAGMA foreign_key_check').all().length) {
      throw new Error('SQLite export failed integrity checks');
    }
    return { format: 'tb-ranking-v1',
      users: db.prepare('SELECT user_id,nickname,token_hash,created_at,updated_at FROM users ORDER BY user_id').all(),
      events: db.prepare('SELECT user_id,problem_key,event_id,accepted_at,accepted_day,difficulty,received_at FROM ac_events ORDER BY user_id,problem_key').all() };
  } finally { db.close(); }
}

if (process.argv[1] && fileURLToPath(import.meta.url).toLowerCase() === resolve(process.argv[1]).toLowerCase()) {
  try {
    const [, , source, destination] = process.argv;
    if (!source || !destination) throw new Error('Usage: node scripts/export-sqlite.mjs sqlite-export.sql migration-data.json');
    const snapshot = snapshotFromSQL(await readFile(source, 'utf8'));
    await writeFile(destination, JSON.stringify(snapshot), { encoding: 'utf8', flag: 'wx', mode: 0o600 });
    process.stdout.write(JSON.stringify({ users: snapshot.users.length, events: snapshot.events.length }) + '\n');
  } catch {
    process.stderr.write('SQLite export conversion failed; check the source dump and use a new output filename\n');
    process.exitCode = 1;
  }
}
