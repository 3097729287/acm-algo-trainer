import { openStore } from '../src/mysql-store.mjs';
import { nicknameKey } from '../src/nicknames.mjs';

const store = await openStore();
try {
  const count = await store.transaction(async connection => {
    const [rows] = await connection.execute('SELECT users.user_id,users.nickname FROM users JOIN accounts USING(user_id) ORDER BY users.created_at,users.user_id FOR UPDATE');
    const names = new Map();
    for (const user of rows) {
      const key = nicknameKey(user.nickname);
      if (names.has(key)) throw new Error('Existing duplicate nicknames require review; no account was renamed.');
      names.set(key, user.user_id);
    }
    const [reserved] = await connection.execute('SELECT nickname_key,user_id FROM account_nicknames FOR UPDATE');
    for (const row of reserved) {
      if (names.get(row.nickname_key) !== row.user_id) throw new Error('Nickname reservations differ; review before migration.');
    }
    for (const [key, owner] of names) await connection.execute('INSERT IGNORE INTO account_nicknames VALUES(?,?)', [key, owner]);
    return rows.length;
  });
  process.stdout.write(JSON.stringify({ migrated: count, identitiesPreserved: true }) + '\n');
} finally { await store.close(); }
