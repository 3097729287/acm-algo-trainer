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
CREATE TABLE social_comment_details(message_id TEXT PRIMARY KEY REFERENCES social_notifications(id) ON DELETE CASCADE,reply_to TEXT REFERENCES social_notifications(id) ON DELETE SET NULL,request_hash TEXT NOT NULL,gift_payload TEXT);
CREATE INDEX social_reply_parent ON social_comment_details(reply_to);

CREATE TABLE account_public_avatars (user_id TEXT PRIMARY KEY REFERENCES accounts(user_id),data TEXT NOT NULL,hash TEXT NOT NULL,updated_at TEXT NOT NULL);
CREATE TABLE training_list_likes (actor_id TEXT NOT NULL REFERENCES users(user_id),list_id TEXT NOT NULL,liked_day TEXT NOT NULL,created_at TEXT NOT NULL,PRIMARY KEY(actor_id,list_id,liked_day));
CREATE INDEX training_list_totals ON training_list_likes(list_id,liked_day);

CREATE TABLE IF NOT EXISTS account_chunk_heads(user_id TEXT PRIMARY KEY REFERENCES accounts(user_id),revision INTEGER NOT NULL,root_hash TEXT NOT NULL,previous_root TEXT,updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS account_chunks(user_id TEXT NOT NULL REFERENCES accounts(user_id),hash TEXT NOT NULL,kind TEXT NOT NULL,payload BLOB NOT NULL,children TEXT NOT NULL,byte_count INTEGER NOT NULL,created_at TEXT NOT NULL,seen_at TEXT NOT NULL,PRIMARY KEY(user_id,hash));

CREATE TABLE IF NOT EXISTS account_chunk_usage(user_id TEXT PRIMARY KEY REFERENCES accounts(user_id),byte_count INTEGER NOT NULL DEFAULT 0,object_count INTEGER NOT NULL DEFAULT 0,last_gc_at TEXT NOT NULL DEFAULT '');
CREATE TABLE account_admin_actions(id INTEGER PRIMARY KEY AUTOINCREMENT,actor_id TEXT NOT NULL,target_id TEXT NOT NULL,action TEXT NOT NULL,created_at TEXT NOT NULL);

CREATE TABLE ranking_leader_schedule(singleton INTEGER PRIMARY KEY,next_day TEXT NOT NULL);
CREATE TABLE ranking_leader_days(period TEXT NOT NULL,ranking_day TEXT NOT NULL,user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,score INTEGER NOT NULL,observed_at TEXT NOT NULL,PRIMARY KEY(period,ranking_day));
CREATE INDEX ranking_leader_owner ON ranking_leader_days(user_id,period,ranking_day);

CREATE TABLE shared_statement_translations(translation_key TEXT PRIMARY KEY,source_url TEXT NOT NULL,source_hash TEXT NOT NULL,source_format TEXT NOT NULL,target_language TEXT NOT NULL,markdown TEXT NOT NULL,contributor_id TEXT REFERENCES users(user_id) ON DELETE SET NULL,created_at TEXT NOT NULL);

CREATE TABLE gameplay_accounts(user_id TEXT PRIMARY KEY REFERENCES accounts(user_id) ON DELETE CASCADE,payload TEXT NOT NULL);
CREATE TABLE gameplay_operations(user_id TEXT NOT NULL REFERENCES accounts(user_id) ON DELETE CASCADE,request_id TEXT NOT NULL,request_hash TEXT NOT NULL,response TEXT NOT NULL,PRIMARY KEY(user_id,request_id));
CREATE TABLE duel_lobby(singleton INTEGER PRIMARY KEY,payload TEXT NOT NULL);
INSERT INTO duel_lobby VALUES(1,'{"queue":[]}');
CREATE TABLE duel_matches(match_id TEXT PRIMARY KEY,payload TEXT NOT NULL);
CREATE TABLE duel_members(user_id TEXT PRIMARY KEY REFERENCES accounts(user_id) ON DELETE CASCADE,match_id TEXT NOT NULL REFERENCES duel_matches(match_id));

CREATE TABLE pk_lobby(singleton INTEGER PRIMARY KEY);
INSERT INTO pk_lobby VALUES(1);
CREATE TABLE pk_ratings(user_id TEXT PRIMARY KEY REFERENCES accounts(user_id) ON DELETE CASCADE,rating INTEGER NOT NULL DEFAULT 1000);
CREATE TABLE pk_queue(user_id TEXT PRIMARY KEY REFERENCES accounts(user_id) ON DELETE CASCADE,ticket TEXT NOT NULL,rating INTEGER NOT NULL,joined_at INTEGER NOT NULL,last_seen INTEGER NOT NULL,min_difficulty INTEGER NOT NULL,max_difficulty INTEGER NOT NULL);
CREATE TABLE pk_matches(match_id TEXT PRIMARY KEY,status TEXT NOT NULL,updated_at INTEGER NOT NULL,due_at INTEGER NOT NULL,payload TEXT NOT NULL);
CREATE TABLE pk_members(user_id TEXT PRIMARY KEY REFERENCES accounts(user_id) ON DELETE CASCADE,match_id TEXT NOT NULL REFERENCES pk_matches(match_id));
CREATE TABLE pk_records(match_id TEXT PRIMARY KEY REFERENCES pk_matches(match_id),player_a TEXT NOT NULL,player_b TEXT NOT NULL,finished_at INTEGER NOT NULL,payload TEXT NOT NULL);
CREATE TABLE pk_operations(user_id TEXT NOT NULL REFERENCES accounts(user_id) ON DELETE CASCADE,request_id TEXT NOT NULL,request_hash TEXT NOT NULL,PRIMARY KEY(user_id,request_id));

CREATE TABLE IF NOT EXISTS account_presence(user_id TEXT PRIMARY KEY REFERENCES accounts(user_id) ON DELETE CASCADE,token_hash TEXT NOT NULL,activity TEXT NOT NULL,last_seen INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS ranked_duel_ratings(user_id TEXT PRIMARY KEY REFERENCES accounts(user_id) ON DELETE CASCADE,rating INTEGER NOT NULL DEFAULT 1000,games INTEGER NOT NULL DEFAULT 0,wins INTEGER NOT NULL DEFAULT 0,updated_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS ranked_duel_records(match_id TEXT PRIMARY KEY REFERENCES duel_matches(match_id),finished_at INTEGER NOT NULL,payload TEXT NOT NULL);
