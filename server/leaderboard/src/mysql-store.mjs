import mysql from 'mysql2/promise';
import { readFile } from 'node:fs/promises';
import { EventConflict } from './errors.mjs';
import { AccountError } from './accounts.mjs';
import { bounds, addDays, rankingQuery, normalizeRank, REWARD_POLICY } from './ranking-rules.mjs';

export async function secret(env, name) {
  if (env[name + '_FILE']) return (await readFile(env[name + '_FILE'], 'utf8')).trim();
  return env[name] || '';
}

export async function openStore(env = process.env) {
  const password = await secret(env, 'MYSQL_PASSWORD');
  if (!password) throw new Error('MYSQL_PASSWORD or MYSQL_PASSWORD_FILE is required');
  const pool = mysql.createPool({ host: env.MYSQL_HOST || 'mysql', port: Number(env.MYSQL_PORT || 3306),
    user: env.MYSQL_USER || 'tb', password, database: env.MYSQL_DATABASE || 'tb_leaderboard',
    charset: 'utf8mb4', timezone: 'Z', connectionLimit: 10, queueLimit: 100,
    connectTimeout: 10000, supportBigNumbers: true, bigNumberStrings: false });
  return new MySQLStore(pool);
}

export class MySQLStore {
  constructor(pool) { this.pool = pool; }
  async health() {
    await this.pool.execute('SELECT 1 FROM official_ac_events LIMIT 0');
    await this.pool.execute('SELECT 1 FROM accounts LIMIT 0');
    await this.pool.execute('SELECT 1 FROM account_sessions LIMIT 0');
  }
  async findUser(id) {
    const [rows] = await this.pool.execute('SELECT users.*,EXISTS(SELECT 1 FROM ranking_admins WHERE ranking_admins.user_id=users.user_id) AS is_admin FROM users WHERE user_id=?', [id]);
    return rows[0] || null;
  }
  async createUser(id, name, hash, timestamp) {
    await this.pool.execute(`INSERT INTO users(user_id,nickname,token_hash,created_at,updated_at) VALUES(?,?,?,?,?)
      ON DUPLICATE KEY UPDATE user_id=user_id`, [id, name, hash, timestamp, timestamp]);
  }
  async updateNickname(id, name, timestamp) {
    await this.pool.execute('UPDATE users SET nickname=?,updated_at=? WHERE user_id=?', [name, timestamp, id]);
  }
  async findAccount(login) {
    const [rows] = await this.pool.execute(`SELECT users.*,accounts.login_id,accounts.password_hash,accounts.password_version,
      EXISTS(SELECT 1 FROM ranking_admins WHERE ranking_admins.user_id=users.user_id) AS is_admin
      FROM accounts JOIN users USING(user_id) WHERE accounts.login_id=?`, [login]);
    return rows[0] || null;
  }
  async findSession(id, hash, now) {
    const [rows] = await this.pool.execute(`SELECT users.*,accounts.login_id,accounts.password_hash,accounts.password_version,
      EXISTS(SELECT 1 FROM ranking_admins WHERE ranking_admins.user_id=users.user_id) AS is_admin
      FROM account_sessions s JOIN accounts USING(user_id) JOIN users USING(user_id)
      WHERE s.user_id=? AND s.token_hash=? AND s.expires_at>? AND s.password_version=accounts.password_version`, [id, hash, now]);
    return rows[0] || null;
  }
  async createAccount(value) {
    try {
      await this.transaction(async connection => {
        if (value.legacyHash) {
          const [rows] = await connection.execute('SELECT token_hash FROM users WHERE user_id=? FOR UPDATE', [value.userId]);
          if (rows[0]?.token_hash !== value.legacyHash) throw new AccountError(409, '旧身份已经关联账号，请使用登录号登录');
          await connection.execute('UPDATE users SET nickname=?,token_hash=?,updated_at=? WHERE user_id=?',
            [value.nickname, value.retiredHash, value.timestamp, value.userId]);
        } else {
          await connection.execute('INSERT INTO users VALUES(?,?,?,?,?)',
            [value.userId, value.nickname, value.retiredHash, value.timestamp, value.timestamp]);
        }
        await connection.execute('INSERT INTO accounts VALUES(?,?,?,1,?,?)',
          [value.userId, value.loginId, value.passwordHash, value.timestamp, value.timestamp]);
      });
    } catch (error) {
      if (error.code === 'ER_DUP_ENTRY') throw new AccountError(409, '登录号已被注册，或旧身份已关联账号');
      throw error;
    }
  }
  createSession(user, session, timestamp) {
    return this.transaction(async connection => {
      const [rows] = await connection.execute('SELECT password_hash,password_version FROM accounts WHERE user_id=? FOR UPDATE', [user.user_id]);
      if (rows[0]?.password_hash !== user.password_hash) throw new AccountError(401, '账号密码已变更，请重新登录');
      await connection.execute('INSERT INTO account_sessions VALUES(?,?,?,?,?)',
        [session.hash, user.user_id, rows[0].password_version, session.expiresAt, timestamp]);
    });
  }
  async deleteSession(hash) { await this.pool.execute('DELETE FROM account_sessions WHERE token_hash=?', [hash]); }
  changePassword(user, encoded, session, timestamp) {
    return this.transaction(async connection => {
      const [result] = await connection.execute('UPDATE accounts SET password_hash=?,password_version=password_version+1,updated_at=? WHERE user_id=? AND password_hash=? AND password_version=?',
        [encoded, timestamp, user.user_id, user.password_hash, user.password_version]);
      if (result.affectedRows !== 1) throw new AccountError(409, '密码已变更，请重新登录');
      await connection.execute('DELETE FROM account_sessions WHERE user_id=?', [user.user_id]);
      await connection.execute('INSERT INTO account_sessions VALUES(?,?,?,?,?)',
        [session.hash, user.user_id, user.password_version + 1, session.expiresAt, timestamp]);
    });
  }
  async transaction(action) {
    const connection = await this.pool.getConnection();
    try {
      await connection.beginTransaction();
      const result = await action(connection);
      await connection.commit();
      return result;
    } catch (error) { await connection.rollback(); throw error; }
    finally { connection.release(); }
  }
  incrementLimit(bucket, expiresAt) {
    return this.transaction(async connection => {
      await connection.execute(`INSERT INTO request_limits(bucket,count,expires_at) VALUES(?,1,?)
        ON DUPLICATE KEY UPDATE count=count+1`, [bucket, expiresAt]);
      const [rows] = await connection.execute('SELECT count FROM request_limits WHERE bucket=?', [bucket]);
      return Number(rows[0].count);
    });
  }
  async rankings(id, range) {
    const { sql, values } = rankingQuery(range);
    const [rows] = await this.pool.execute(sql + ' SELECT * FROM ranked ORDER BY position LIMIT 100', values);
    const [own] = await this.pool.execute(sql + ' SELECT * FROM ranked WHERE user_id=?', [...values, id]);
    return { rows: rows.map(normalizeRank), own: normalizeRank(own[0]) || null };
  }
  settleRewards(now) {
    return this.transaction(async connection => {
      const day = bounds('daily', now).start, week = bounds('weekly', now).start;
      await connection.execute('INSERT INTO ranking_schedule VALUES(1,?,?) ON DUPLICATE KEY UPDATE singleton=singleton', [day, week]);
      const [settings] = await connection.execute('SELECT * FROM ranking_schedule WHERE singleton=1 FOR UPDATE');
      const timestamp = new Date(now).toISOString();
      for (const [period, cutoff, step] of [['daily', day, 1], ['weekly', week, 7]]) {
        let start = settings[0][period + '_start'];
        while (start < cutoff) {
          const end = addDays(start, step);
          const { sql, values } = rankingQuery({ start, end });
          const [winners] = await connection.execute(sql + ' SELECT * FROM ranked WHERE position<=3 ORDER BY position', values);
          await connection.execute('INSERT INTO ranking_cycles VALUES(?,?,?,?)', [period, start, end, timestamp]);
          for (const row of winners) {
            await connection.execute('INSERT INTO ranking_rewards VALUES(?,?,?,?,?,?,?)',
              [row.user_id, period, start, end, Number(row.position), REWARD_POLICY[period][Number(row.position)-1], timestamp]);
          }
          start = end;
        }
        await connection.execute(`UPDATE ranking_schedule SET ${period}_start=? WHERE singleton=1`, [start]);
      }
    });
  }
  async rewards(id) {
    const [rows] = await this.pool.execute('SELECT COALESCE(SUM(xp),0) AS totalXp FROM ranking_rewards WHERE user_id=?', [id]);
    const [awards] = await this.pool.execute('SELECT period,start_date AS startDate,end_date AS endDate,position AS `rank`,xp,settled_at AS awardedAt FROM ranking_rewards WHERE user_id=? ORDER BY settled_at DESC,start_date DESC,period LIMIT 50', [id]);
    return { userId: id, totalXp: Number(rows[0].totalXp), awards };
  }
  removeRankings(actor, target, period, range, timestamp) {
    return this.transaction(async connection => {
      // Re-check the role in the same transaction as the write.
      const [role] = await connection.execute('SELECT user_id FROM ranking_admins WHERE user_id=? FOR SHARE', [actor]);
      if (!role.length) throw new Error('Administrator role required');
      const filters = [], values = [];
      if (target) { filters.push('e.user_id=?'); values.push(target); }
      if (range) { filters.push('e.accepted_day>=? AND e.accepted_day<?'); values.push(range.start, range.end); }
      const [result] = await connection.execute(`INSERT IGNORE INTO ranking_exclusions(user_id,problem_key,deleted_at)
        SELECT e.user_id,e.problem_key,? FROM official_ac_events e ${filters.length ? 'WHERE '+filters.join(' AND ') : ''}`, [timestamp, ...values]);
      const removed = Number(result.affectedRows);
      await connection.execute('INSERT INTO ranking_admin_actions(actor_id,target_id,period,start_date,end_date,removed_count,created_at) VALUES(?,?,?,?,?,?,?)',
        [actor, target, period, range?.start ?? null, range?.end ?? null, removed, timestamp]);
      return { removed, period, userId: target };
    });
  }
  async recordEvents(id, events, timestamp) {
    try {
      await this.transaction(async connection => {
        // Serialize batches for one identity. Distinct users can still write concurrently.
        await connection.execute('SELECT user_id FROM users WHERE user_id=? FOR UPDATE', [id]);
        for (const item of events) {
          const [rows] = await connection.execute('SELECT accepted_at,accepted_day,difficulty FROM official_ac_events WHERE user_id=? AND problem_key=?', [id, item.problemKey]);
          const previous = rows[0];
          if (previous) {
            const earlier = item.acceptedAt < previous.accepted_at;
            await connection.execute('UPDATE official_ac_events SET accepted_at=?,accepted_day=?,difficulty=? WHERE user_id=? AND problem_key=?',
              [earlier ? item.acceptedAt : previous.accepted_at, earlier ? item.day : previous.accepted_day,
                previous.difficulty ?? item.difficulty ?? null, id, item.problemKey]);
          } else {
            // A duplicate event ID for a different problem must fail and roll back the batch.
            await connection.execute(`INSERT INTO official_ac_events(user_id,problem_key,event_id,accepted_at,accepted_day,difficulty,received_at)
              VALUES(?,?,?,?,?,?,?)`, [id, item.problemKey, item.eventId, item.acceptedAt, item.day, item.difficulty ?? null, timestamp]);
          }
        }
      });
    } catch (error) {
      if (error.code === 'ER_DUP_ENTRY') throw new EventConflict();
      throw error;
    }
  }
  async cleanup(now) {
    await this.pool.execute('DELETE FROM request_limits WHERE expires_at<?', [now]);
    await this.pool.execute('DELETE FROM account_sessions WHERE expires_at<=?', [now]);
  }
  close() { return this.pool.end(); }
}
