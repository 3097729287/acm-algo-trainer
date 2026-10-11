import mysql from 'mysql2/promise';
import { readFile } from 'node:fs/promises';
import { EventConflict } from './errors.mjs';

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
  async health() { await this.pool.execute('SELECT 1 FROM official_ac_events LIMIT 0'); }
  async findUser(id) {
    const [rows] = await this.pool.execute('SELECT * FROM users WHERE user_id=?', [id]);
    return rows[0] || null;
  }
  async createUser(id, name, hash, timestamp) {
    await this.pool.execute(`INSERT INTO users(user_id,nickname,token_hash,created_at,updated_at) VALUES(?,?,?,?,?)
      ON DUPLICATE KEY UPDATE user_id=user_id`, [id, name, hash, timestamp, timestamp]);
  }
  async updateNickname(id, name, timestamp) {
    await this.pool.execute('UPDATE users SET nickname=?,updated_at=? WHERE user_id=?', [name, timestamp, id]);
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
    const where = range ? 'WHERE accepted_day>=? AND accepted_day<?' : '';
    const values = range ? [range.start, range.end] : [];
    // RANK is reserved in MySQL; expose the protocol's rank field after the query.
    const cte = `WITH counts AS (SELECT user_id,COUNT(*) AS count FROM official_ac_events ${where} GROUP BY user_id),
      ranked AS (SELECT users.user_id,users.nickname,counts.count,
        RANK() OVER(ORDER BY counts.count DESC) AS position FROM counts JOIN users USING(user_id))`;
    const normalize = row => row && ({ ...row, count: Number(row.count), rank: Number(row.position) });
    const [rows] = await this.pool.execute(cte + ' SELECT * FROM ranked ORDER BY count DESC,user_id LIMIT 100', values);
    const [own] = await this.pool.execute(cte + ' SELECT * FROM ranked WHERE user_id=?', [...values, id]);
    return { rows: rows.map(normalize), own: normalize(own[0]) || null };
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
  async cleanup(now) { await this.pool.execute('DELETE FROM request_limits WHERE expires_at<?', [now]); }
  close() { return this.pool.end(); }
}
