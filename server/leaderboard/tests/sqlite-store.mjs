// Test-only SQLite store for exercising the production API protocol offline.
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { EventConflict } from '../src/errors.mjs';
import { bounds, addDays, rankingQuery, normalizeRank, REWARD_POLICY } from '../src/ranking-rules.mjs';

export class SQLiteStore {
  constructor(path = ':memory:') {
    this.database = new DatabaseSync(path);
    this.database.exec('PRAGMA foreign_keys=ON');
    if (!this.database.prepare("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").get()) {
      this.database.exec(readFileSync(new URL('./schema.sql', import.meta.url), 'utf8'));
    }
  }
  async health() { this.database.prepare('SELECT 1').get(); }
  async findUser(id) { return this.database.prepare('SELECT users.*,EXISTS(SELECT 1 FROM ranking_admins WHERE ranking_admins.user_id=users.user_id) AS is_admin FROM users WHERE user_id=?').get(id) || null; }
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
    const { sql, values } = rankingQuery(range);
    return {
      rows: this.database.prepare(sql + ' SELECT * FROM ranked ORDER BY position LIMIT 100').all(...values).map(normalizeRank),
      own: normalizeRank(this.database.prepare(sql + ' SELECT * FROM ranked WHERE user_id=?').get(...values, id)) || null,
    };
  }
  async settleRewards(now) {
    this.database.exec('BEGIN IMMEDIATE');
    try {
      const day = bounds('daily', now).start, week = bounds('weekly', now).start, timestamp = new Date(now).toISOString();
      this.database.prepare('INSERT OR IGNORE INTO ranking_schedule VALUES(1,?,?)').run(day, week);
      const settings = this.database.prepare('SELECT * FROM ranking_schedule WHERE singleton=1').get();
      for (const [period, cutoff, step] of [['daily', day, 1], ['weekly', week, 7]]) {
        let start = settings[period + '_start'];
        while (start < cutoff) {
          const end = addDays(start, step), { sql, values } = rankingQuery({ start, end });
          const winners = this.database.prepare(sql + ' SELECT * FROM ranked WHERE position<=3 ORDER BY position').all(...values);
          this.database.prepare('INSERT INTO ranking_cycles VALUES(?,?,?,?)').run(period, start, end, timestamp);
          for (const row of winners) this.database.prepare('INSERT INTO ranking_rewards VALUES(?,?,?,?,?,?,?)').run(row.user_id, period, start, end, row.position, REWARD_POLICY[period][row.position-1], timestamp);
          start = end;
        }
        this.database.prepare(`UPDATE ranking_schedule SET ${period}_start=? WHERE singleton=1`).run(start);
      }
      this.database.exec('COMMIT');
    } catch (error) { this.database.exec('ROLLBACK'); throw error; }
  }
  async rewards(id) {
    const totalXp = this.database.prepare('SELECT COALESCE(SUM(xp),0) AS totalXp FROM ranking_rewards WHERE user_id=?').get(id).totalXp;
    const awards = this.database.prepare('SELECT period,start_date AS startDate,end_date AS endDate,position AS rank,xp,settled_at AS awardedAt FROM ranking_rewards WHERE user_id=? ORDER BY settled_at DESC,start_date DESC,period LIMIT 50').all(id);
    return { userId: id, totalXp, awards };
  }
  async removeRankings(actor, target, period, range, timestamp) {
    this.database.exec('BEGIN IMMEDIATE');
    try {
      if (!this.database.prepare('SELECT user_id FROM ranking_admins WHERE user_id=?').get(actor)) throw new Error('Administrator role required');
      const filters = [], values = [];
      if (target) { filters.push('e.user_id=?'); values.push(target); }
      if (range) { filters.push('e.accepted_day>=? AND e.accepted_day<?'); values.push(range.start, range.end); }
      const removed = this.database.prepare(`INSERT OR IGNORE INTO ranking_exclusions(user_id,problem_key,deleted_at) SELECT e.user_id,e.problem_key,? FROM official_ac_events e ${filters.length ? 'WHERE '+filters.join(' AND ') : ''}`).run(timestamp, ...values).changes;
      this.database.prepare('INSERT INTO ranking_admin_actions(actor_id,target_id,period,start_date,end_date,removed_count,created_at) VALUES(?,?,?,?,?,?,?)').run(actor, target, period, range?.start ?? null, range?.end ?? null, removed, timestamp);
      this.database.exec('COMMIT');
      return { removed, period, userId: target };
    } catch (error) { this.database.exec('ROLLBACK'); throw error; }
  }
  async recordEvents(id, events, timestamp) {
    this.database.exec('BEGIN IMMEDIATE');
    try {
      const statement = this.database.prepare(`INSERT INTO official_ac_events(user_id,problem_key,event_id,accepted_at,accepted_day,difficulty,received_at)
        VALUES(?,?,?,?,?,?,?) ON CONFLICT(user_id,problem_key) DO UPDATE SET
        accepted_day=CASE WHEN excluded.accepted_at<official_ac_events.accepted_at THEN excluded.accepted_day ELSE official_ac_events.accepted_day END,
        accepted_at=MIN(official_ac_events.accepted_at,excluded.accepted_at),
        difficulty=COALESCE(official_ac_events.difficulty,excluded.difficulty)`);
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
