PRAGMA foreign_keys = ON;

CREATE TABLE users (
  user_id TEXT PRIMARY KEY,
  nickname TEXT NOT NULL,
  token_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE account_nicknames (
  nickname_key TEXT PRIMARY KEY,
  user_id TEXT NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE
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

CREATE TABLE accounts (
  user_id TEXT PRIMARY KEY REFERENCES users(user_id), login_id TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL, password_version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE account_sessions (
  token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES accounts(user_id),
  password_version INTEGER NOT NULL, expires_at INTEGER NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX sessions_expiry ON account_sessions(expires_at);
CREATE TABLE account_state (user_id TEXT PRIMARY KEY REFERENCES accounts(user_id),revision INTEGER NOT NULL,payload TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE account_login_days (user_id TEXT NOT NULL REFERENCES accounts(user_id),day TEXT NOT NULL,first_seen_at TEXT NOT NULL,PRIMARY KEY(user_id,day));
CREATE INDEX login_days_day ON account_login_days(day,user_id);
CREATE TABLE account_public_progress (user_id TEXT PRIMARY KEY REFERENCES accounts(user_id),payload TEXT NOT NULL,updated_at TEXT NOT NULL);

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
CREATE TABLE social_likes (actor_id TEXT NOT NULL REFERENCES users(user_id),recipient_id TEXT NOT NULL REFERENCES users(user_id),liked_day TEXT NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(actor_id,recipient_id,liked_day));
CREATE INDEX social_like_recipient ON social_likes(recipient_id,liked_day);
CREATE TABLE social_notifications (id TEXT PRIMARY KEY,kind TEXT NOT NULL,actor_id TEXT NOT NULL REFERENCES users(user_id),recipient_id TEXT NOT NULL REFERENCES users(user_id),body TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL,read_at TEXT);
CREATE INDEX social_inbox ON social_notifications(recipient_id,created_at);

CREATE TABLE account_public_avatars (user_id TEXT PRIMARY KEY REFERENCES accounts(user_id),data TEXT NOT NULL,hash TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE training_list_likes (actor_id TEXT NOT NULL REFERENCES users(user_id),list_id TEXT NOT NULL,liked_day TEXT NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(actor_id,list_id,liked_day));
CREATE INDEX training_list_totals ON training_list_likes(list_id,liked_day);

CREATE TABLE IF NOT EXISTS account_chunk_heads(user_id TEXT PRIMARY KEY REFERENCES accounts(user_id),revision INTEGER NOT NULL,root_hash TEXT NOT NULL,previous_root TEXT,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS account_chunks(user_id TEXT NOT NULL REFERENCES accounts(user_id),hash TEXT NOT NULL,kind TEXT NOT NULL,payload BLOB NOT NULL,children TEXT NOT NULL,byte_count INTEGER NOT NULL,created_at TEXT NOT NULL,seen_at TEXT NOT NULL,PRIMARY KEY(user_id,hash));

CREATE TABLE IF NOT EXISTS account_chunk_usage(user_id TEXT PRIMARY KEY REFERENCES accounts(user_id),byte_count INTEGER NOT NULL DEFAULT 0,object_count INTEGER NOT NULL DEFAULT 0,last_gc_at TEXT NOT NULL DEFAULT '');
