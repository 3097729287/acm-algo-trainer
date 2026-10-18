import { createHash } from 'node:crypto';
import { AccountError } from './accounts.mjs';

export function nicknameKey(name) {
  const normalized = name.normalize('NFKC').trim().replace(/\s+/gu, ' ').toLowerCase();
  if (!normalized) throw new AccountError(400, '请填写昵称');
  return createHash('sha256').update(normalized).digest('hex');
}

export async function claimNickname(connection, userId, name, replacing = true) {
  try {
    const key = nicknameKey(name);
    // Deleting a nonexistent secondary key takes a gap lock in InnoDB.
    // Concurrent registrations must insert directly so only the winning
    // normalized name is committed; renames update their existing reservation.
    const [current] = replacing ? await connection.execute('SELECT nickname_key FROM account_nicknames WHERE user_id=? FOR UPDATE', [userId]) : [[]];
    if (current.length) await connection.execute('UPDATE account_nicknames SET nickname_key=? WHERE user_id=?', [key, userId]);
    else await connection.execute('INSERT INTO account_nicknames(nickname_key,user_id) VALUES(?,?)', [key, userId]);
  } catch (error) {
    if (error.code === 'ER_DUP_ENTRY') throw new AccountError(409, '昵称已被使用，请换一个');
    if (error.code === 'ER_LOCK_DEADLOCK') throw new AccountError(409, '昵称正在被修改，请重试');
    throw error;
  }
}
