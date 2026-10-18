// Test-only SQLite store for exercising the production API protocol offline.
import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { EventConflict } from '../src/errors.mjs';
import { AccountError } from '../src/accounts.mjs';
import { nicknameKey } from '../src/nicknames.mjs';
import { storedPublicProgress } from '../src/public-progress.mjs';
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
  claimNickname(id, name) {
    this.database.prepare('DELETE FROM account_nicknames WHERE user_id=?').run(id);
    try { this.database.prepare('INSERT INTO account_nicknames VALUES(?,?)').run(nicknameKey(name), id); }
    catch (error) {
      if (/UNIQUE constraint/i.test(String(error))) throw new AccountError(409, '昵称已被使用，请换一个');
      throw error;
    }
  }
  async findUser(id) { return this.database.prepare('SELECT users.*,EXISTS(SELECT 1 FROM ranking_admins WHERE ranking_admins.user_id=users.user_id) AS is_admin FROM users WHERE user_id=?').get(id) || null; }
  async createUser(id, name, hash, timestamp) {
    this.database.prepare('INSERT OR IGNORE INTO users(user_id,nickname,token_hash,created_at,updated_at) VALUES(?,?,?,?,?)')
      .run(id, name, hash, timestamp, timestamp);
  }
  async updateNickname(id, name, timestamp) {
    this.database.prepare('UPDATE users SET nickname=?,updated_at=? WHERE user_id=?').run(name, timestamp, id);
  }
  async publicProgress(id) {
    return storedPublicProgress(this.database.prepare('SELECT payload FROM account_public_progress WHERE user_id=?').get(id)?.payload);
  }
  async savePublicProfile(id, hash, now, name, progress, timestamp) {
    return this.transaction(() => {
      if (!this.database.prepare('SELECT 1 FROM account_sessions WHERE user_id=? AND token_hash=? AND expires_at>?').get(id, hash, now))
        throw new AccountError(401, '账号已在另一台设备登录，请重新登录');
      if (name !== null) {
        this.claimNickname(id, name);
        this.database.prepare('UPDATE users SET nickname=?,updated_at=? WHERE user_id=?').run(name, timestamp, id);
      }
      if (progress !== null) this.database.prepare('INSERT INTO account_public_progress VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET payload=excluded.payload,updated_at=excluded.updated_at')
        .run(id, JSON.stringify(progress), timestamp);
    });
  }
  async findAccount(login) {
    return this.database.prepare(`SELECT users.*,accounts.login_id,accounts.password_hash,accounts.password_version,
      EXISTS(SELECT 1 FROM ranking_admins WHERE ranking_admins.user_id=users.user_id) AS is_admin
      FROM accounts JOIN users USING(user_id) WHERE login_id=?`).get(login) || null;
  }
  async findSession(id, hash, now) {
    return this.database.prepare(`SELECT users.*,accounts.login_id,accounts.password_hash,accounts.password_version,
      EXISTS(SELECT 1 FROM ranking_admins WHERE ranking_admins.user_id=users.user_id) AS is_admin
      FROM account_sessions s JOIN accounts USING(user_id) JOIN users USING(user_id)
      WHERE s.user_id=? AND s.token_hash=? AND s.expires_at>? AND s.password_version=accounts.password_version`).get(id, hash, now) || null;
  }
  transaction(action) {
    this.database.exec('BEGIN IMMEDIATE');
    try { const value = action(); this.database.exec('COMMIT'); return value; }
    catch (error) { this.database.exec('ROLLBACK'); throw error; }
  }
  async createAccount(value) {
    try {
      this.transaction(() => {
        if (value.legacyHash) {
          const row = this.database.prepare('SELECT token_hash FROM users WHERE user_id=?').get(value.userId);
          if (row?.token_hash !== value.legacyHash) throw new AccountError(409, '旧身份已经关联账号，请使用登录号登录');
          this.database.prepare('UPDATE users SET nickname=?,token_hash=?,updated_at=? WHERE user_id=?')
            .run(value.nickname, value.retiredHash, value.timestamp, value.userId);
        } else this.database.prepare('INSERT INTO users VALUES(?,?,?,?,?)')
          .run(value.userId, value.nickname, value.retiredHash, value.timestamp, value.timestamp);
        this.database.prepare('INSERT INTO accounts VALUES(?,?,?,1,?,?)')
          .run(value.userId, value.loginId, value.passwordHash, value.timestamp, value.timestamp);
        this.claimNickname(value.userId, value.nickname);
      });
    } catch (error) {
      if (/UNIQUE constraint/i.test(String(error))) throw new AccountError(409, '登录号已被注册，或旧身份已关联账号');
      throw error;
    }
  }
  async createSession(user, session, timestamp, stateProtocol = false) {
    this.transaction(() => {
      const row = this.database.prepare('SELECT password_hash,password_version FROM accounts WHERE user_id=?').get(user.user_id);
      if (row?.password_hash !== user.password_hash) throw new AccountError(401, '账号密码已变更，请重新登录');
      const state = this.database.prepare('SELECT revision FROM account_state WHERE user_id=?').get(user.user_id);
      if (!stateProtocol && Number(state?.revision || 0) > 0)
        throw new AccountError(426, '该账号已启用跨电脑同步，请升级 TB 至 1.0.20 或更新版本后登录');
      this.database.prepare('DELETE FROM account_sessions WHERE user_id=?').run(user.user_id);
      this.database.prepare('INSERT INTO account_sessions VALUES(?,?,?,?,?)')
        .run(session.hash, user.user_id, row.password_version, session.expiresAt, timestamp);
      this.database.prepare('INSERT OR IGNORE INTO account_login_days VALUES(?,?,?)').run(user.user_id, bounds('daily', Date.parse(timestamp)).day, timestamp);
    });
  }
  async deleteSession(hash) { this.database.prepare('DELETE FROM account_sessions WHERE token_hash=?').run(hash); }
  async changePassword(user, encoded, session, timestamp) {
    this.transaction(() => {
      const result = this.database.prepare('UPDATE accounts SET password_hash=?,password_version=password_version+1,updated_at=? WHERE user_id=? AND password_hash=? AND password_version=?')
        .run(encoded, timestamp, user.user_id, user.password_hash, user.password_version);
      if (result.changes !== 1) throw new AccountError(409, '密码已变更，请重新登录');
      this.database.prepare('DELETE FROM account_sessions WHERE user_id=?').run(user.user_id);
      this.database.prepare('INSERT INTO account_sessions VALUES(?,?,?,?,?)')
        .run(session.hash, user.user_id, user.password_version + 1, session.expiresAt, timestamp);
    });
  }
  async incrementLimit(bucket, expiresAt) {
    return this.database.prepare(`INSERT INTO request_limits(bucket,count,expires_at) VALUES(?,1,?)
      ON CONFLICT(bucket) DO UPDATE SET count=count+1 RETURNING count`).get(bucket, expiresAt).count;
  }
  async rankings(id, range, loginDay) {
    const { sql, values } = rankingQuery(range, loginDay);
    const enriched = ' SELECT ranked.*,p.payload AS public_progress FROM ranked LEFT JOIN account_public_progress p ON p.user_id=ranked.user_id';
    const rows = this.database.prepare(sql + enriched + ' WHERE ranked.position<=100 OR ranked.user_id=? ORDER BY position').all(...values, id).map(normalizeRank);
    return { rows: rows.filter(row => row.rank <= 100), own: rows.find(row => row.user_id === id) || null };
  }
  async recordLogin(id, day, timestamp) {
    this.database.prepare('INSERT OR IGNORE INTO account_login_days VALUES(?,?,?)').run(id, day, timestamp);
  }
  async stateRevision(id) { return this.database.prepare('SELECT revision FROM account_state WHERE user_id=?').get(id)?.revision || 0; }
  async accountState(id) {
    const row = this.database.prepare('SELECT revision,payload FROM account_state WHERE user_id=?').get(id);
    return { revision: row?.revision || 0, state: row ? JSON.parse(row.payload) : null };
  }
  async saveAccountState(id, hash, now, revision, state, timestamp) {
    return this.transaction(() => {
      if (!this.database.prepare('SELECT 1 FROM account_sessions WHERE user_id=? AND token_hash=? AND expires_at>?').get(id, hash, now))
        throw new AccountError(401, '账号已在另一台设备登录，请重新登录');
      const previous = this.database.prepare('SELECT revision FROM account_state WHERE user_id=?').get(id)?.revision || 0;
      if (previous !== revision) throw new AccountError(409, '账号数据已更新，请重新同步');
      this.database.prepare('INSERT INTO account_state VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET revision=excluded.revision,payload=excluded.payload,updated_at=excluded.updated_at')
        .run(id, revision + 1, JSON.stringify(state), timestamp);
      return { revision: revision + 1, savedAt: timestamp };
    });
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
  async cleanup(now) {
    this.database.prepare('DELETE FROM request_limits WHERE expires_at<?').run(now);
    this.database.prepare('DELETE FROM account_sessions WHERE expires_at<=?').run(now);
  }
  async close() { this.database.close(); }
}
