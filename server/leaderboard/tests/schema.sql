PRAGMA foreign_keys = ON;

CREATE TABLE users (
  user_id TEXT PRIMARY KEY,
  nickname TEXT NOT NULL,
  token_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE ac_events (
  user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  problem_key TEXT NOT NULL,
  event_id TEXT NOT NULL,
  accepted_at TEXT NOT NULL,
  accepted_day TEXT NOT NULL,
  difficulty REAL,
  received_at TEXT NOT NULL,
  PRIMARY KEY(user_id, problem_key),
  UNIQUE(user_id, event_id)
);
CREATE INDEX ac_events_day_user ON ac_events(accepted_day, user_id);

CREATE TABLE request_limits (
  bucket TEXT PRIMARY KEY,
  count INTEGER NOT NULL,
  expires_at INTEGER NOT NULL
);
CREATE INDEX request_limits_expiry ON request_limits(expires_at);

CREATE TABLE official_ac_events (
  user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  problem_key TEXT NOT NULL,
  event_id TEXT NOT NULL,
  accepted_at TEXT NOT NULL,
  accepted_day TEXT NOT NULL,
  difficulty REAL,
  received_at TEXT NOT NULL,
  PRIMARY KEY(user_id, problem_key),
  UNIQUE(user_id, event_id)
);

CREATE TABLE ranking_admins (user_id TEXT PRIMARY KEY REFERENCES users(user_id),granted_at TEXT NOT NULL);
CREATE TABLE ranking_exclusions (user_id TEXT NOT NULL,problem_key TEXT NOT NULL,deleted_at TEXT NOT NULL,PRIMARY KEY(user_id,problem_key),FOREIGN KEY(user_id,problem_key) REFERENCES official_ac_events(user_id,problem_key));
CREATE TABLE ranking_schedule (singleton INTEGER PRIMARY KEY,daily_start TEXT NOT NULL,weekly_start TEXT NOT NULL);
CREATE TABLE ranking_cycles (period TEXT NOT NULL,start_date TEXT NOT NULL,end_date TEXT NOT NULL,settled_at TEXT NOT NULL,PRIMARY KEY(period,start_date));
CREATE TABLE ranking_rewards (user_id TEXT NOT NULL REFERENCES users(user_id),period TEXT NOT NULL,start_date TEXT NOT NULL,end_date TEXT NOT NULL,position INTEGER NOT NULL,xp INTEGER NOT NULL,settled_at TEXT NOT NULL,PRIMARY KEY(user_id,period,start_date),FOREIGN KEY(period,start_date) REFERENCES ranking_cycles(period,start_date));
CREATE TABLE ranking_admin_actions (id INTEGER PRIMARY KEY AUTOINCREMENT,actor_id TEXT NOT NULL,target_id TEXT,period TEXT NOT NULL,start_date TEXT,end_date TEXT,removed_count INTEGER NOT NULL,created_at TEXT NOT NULL);
