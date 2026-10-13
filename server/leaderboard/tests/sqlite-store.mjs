// Test-only SQLite store for exercising the production API protocol offline.
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { EventConflict } from '../src/errors.mjs';

export class SQLiteStore {
  constructor(path = ':memory:') {
    this.database = new DatabaseSync(path);
    this.database.exec('PRAGMA foreign_keys=ON');
    if (!this.database.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").get()) {
      this.database.exec(readFileSync(new URL('./schema.sql', import.meta.url), 'utf8'));
    }
  }
  async health() { this.database.prepare('SELECT 1').get(); }
  async findUser(id) { return this.database.prepare('SELECT * FROM users WHERE user_id=?').get(id) || null; }
  async createUser(id, name, hash, timestamp) {
    this.database.prepare('INSERT OR IGNORE INTO users(user_id,nickname,token_hash,created_at,updated_at) VALUES(?,?,?,?,?)')
      .run(id, name, hash, timestamp, timestamp);
  }
  async updateNickname(id, name, timestamp) {
    this.database.prepare('UPDATE users SET nickname=?,updated_at=? WHERE user_id=?').run(name, timestamp, id);
  }
  async incrementLimit(bucket, expiresAt) {
    return this.database.prepare(`INSERT INTO request_limits(bucket,count,expires_at) VALUES(?,1,?)
      ON CONFLICT(bucket) DO UPDATE SET count=count+1 RETURNING count`).get(bucket, expiresAt).count;
  }
  async rankings(id, range) {
    const where = range ? 'WHERE accepted_day>=? AND accepted_day<?' : '';
    const values = range ? [range.start, range.end] : [];
    const cte = `WITH counts AS (SELECT user_id,COUNT(*) AS count FROM ac_events ${where} GROUP BY user_id),
      ranked AS (SELECT users.user_id,users.nickname,counts.count,
        RANK() OVER(ORDER BY counts.count DESC) AS rank FROM counts JOIN users USING(user_id))`;
    return {
      rows: this.database.prepare(cte + ' SELECT * FROM ranked ORDER BY count DESC,user_id LIMIT 100').all(...values),
      own: this.database.prepare(cte + ' SELECT * FROM ranked WHERE user_id=?').get(...values, id) || null,
    };
  }
  async recordEvents(id, events, timestamp) {
    this.database.exec('BEGIN IMMEDIATE');
    try {
      const statement = this.database.prepare(`INSERT INTO ac_events(user_id,problem_key,event_id,accepted_at,accepted_day,difficulty,received_at)
        VALUES(?,?,?,?,?,?,?) ON CONFLICT(user_id,problem_key) DO UPDATE SET
        accepted_day=CASE WHEN excluded.accepted_at<ac_events.accepted_at THEN excluded.accepted_day ELSE ac_events.accepted_day END,
        accepted_at=MIN(ac_events.accepted_at,excluded.accepted_at),
        difficulty=COALESCE(ac_events.difficulty,excluded.difficulty)`);
      for (const item of events) statement.run(id, item.problemKey, item.eventId, item.acceptedAt, item.day, item.difficulty ?? null, timestamp);
      this.database.exec('COMMIT');
    } catch (error) {
      this.database.exec('ROLLBACK');
      if (/UNIQUE constraint/i.test(String(error))) throw new EventConflict();
      throw error;
    }
  }
  async cleanup(now) { this.database.prepare('DELETE FROM request_limits WHERE expires_at<?').run(now); }
  async close() { this.database.close(); }
}
