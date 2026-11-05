CREATE TABLE IF NOT EXISTS training (
              id TEXT PRIMARY KEY, active_at TEXT NOT NULL, solution_pending INTEGER NOT NULL DEFAULT 0,
              rewrite_due INTEGER NOT NULL DEFAULT 0, accepted_at TEXT, last_local_at TEXT,
              last_review_at TEXT, review_count INTEGER NOT NULL DEFAULT 0, mock_due INTEGER NOT NULL DEFAULT 0,
              solution_seen_at TEXT, mock_due_at TEXT, mock_due_context TEXT);
            CREATE TABLE IF NOT EXISTS practice_sets (
              id TEXT PRIMARY KEY, name TEXT NOT NULL UNIQUE, ids TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS contests (
              id TEXT PRIMARY KEY, name TEXT NOT NULL, status TEXT NOT NULL, started_at TEXT NOT NULL,
              deadline TEXT NOT NULL, finished_at TEXT, duration INTEGER NOT NULL, slots TEXT NOT NULL);
            CREATE UNIQUE INDEX IF NOT EXISTS one_running_contest ON contests(status) WHERE status='running';
            CREATE TABLE IF NOT EXISTS drafts (
              problem_id TEXT NOT NULL, context TEXT NOT NULL, code TEXT NOT NULL, saved_at TEXT NOT NULL,
              PRIMARY KEY(problem_id,context));
            CREATE TABLE IF NOT EXISTS submissions (
              id TEXT PRIMARY KEY, problem_id TEXT NOT NULL, contest_id TEXT, mode TEXT NOT NULL,
              code TEXT NOT NULL, submitted_at TEXT NOT NULL, finished_at TEXT, verdict TEXT NOT NULL,
              scope TEXT NOT NULL, time_ms REAL, memory_kb REAL, passed INTEGER NOT NULL DEFAULT 0,
              total INTEGER NOT NULL DEFAULT 0, output TEXT NOT NULL DEFAULT '', stderr TEXT NOT NULL DEFAULT '',
              message TEXT NOT NULL DEFAULT '', custom_input TEXT NOT NULL DEFAULT '', solution_seen INTEGER NOT NULL DEFAULT 0);
            CREATE INDEX IF NOT EXISTS submission_problem ON submissions(problem_id,submitted_at);
            CREATE INDEX IF NOT EXISTS submission_contest ON submissions(contest_id,submitted_at);

            CREATE TABLE IF NOT EXISTS tb_rank_profile (
              id INTEGER PRIMARY KEY CHECK(id=1), unlocked_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS official_first_xp_awards (
              problem_key TEXT PRIMARY KEY, accepted_at TEXT NOT NULL,
              awarded_xp INTEGER NOT NULL CHECK(awarded_xp >= 0));
            CREATE TABLE IF NOT EXISTS official_xp_state (
              id INTEGER PRIMARY KEY CHECK(id=1), migrated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS achievement_xp_claims (
              achievement_id TEXT PRIMARY KEY, unlocked_at TEXT,
              awarded_xp INTEGER NOT NULL CHECK(awarded_xp>=0), claimed_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS account_preferences (
              key TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS account_problem_facts (
              problem_id TEXT PRIMARY KEY, value TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS account_statement_reading_idx ON account_problem_facts (
              CASE WHEN json_valid(value) THEN json_extract(value,'$.statement.accountReading') ELSE 0 END);
            CREATE TABLE IF NOT EXISTS daily_missions (
              day TEXT NOT NULL, id TEXT NOT NULL, definition TEXT NOT NULL,
              claimed_at TEXT, awarded_xp INTEGER NOT NULL DEFAULT 0, evidence TEXT NOT NULL DEFAULT '[]',
              PRIMARY KEY(day,id));
            CREATE TABLE IF NOT EXISTS goals (
              id TEXT PRIMARY KEY, created_at TEXT NOT NULL, config TEXT NOT NULL,
              archived INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS goal_daily_assignments (
              goal_id TEXT NOT NULL, day TEXT NOT NULL, ids TEXT NOT NULL, target INTEGER, PRIMARY KEY(goal_id,day));
            CREATE TABLE IF NOT EXISTS ranking_profile (
              singleton INTEGER PRIMARY KEY CHECK(singleton=1), user_id TEXT NOT NULL UNIQUE,
              nickname TEXT NOT NULL, auth_token TEXT NOT NULL, endpoint TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL, last_synced_at TEXT);
            CREATE TABLE IF NOT EXISTS ranking_receipts (
              endpoint TEXT NOT NULL, event_id TEXT NOT NULL, accepted_at TEXT NOT NULL,
              PRIMARY KEY(endpoint,event_id));
            CREATE TABLE IF NOT EXISTS ranking_reward_totals (
              endpoint TEXT NOT NULL,user_id TEXT NOT NULL,total_xp INTEGER NOT NULL,
              awards TEXT NOT NULL DEFAULT '[]',updated_at TEXT NOT NULL,
              PRIMARY KEY(endpoint,user_id));
            CREATE TABLE IF NOT EXISTS official_pending (
              id TEXT PRIMARY KEY, session_id TEXT NOT NULL, submission_id TEXT NOT NULL,
              problem_id TEXT, url TEXT, code TEXT, platform TEXT, accepted_at TEXT);

ALTER TABLE training ADD COLUMN active INTEGER NOT NULL DEFAULT 1;
ALTER TABLE training ADD COLUMN removed_at TEXT;
ALTER TABLE submissions ADD COLUMN sample_run INTEGER NOT NULL DEFAULT 0;
ALTER TABLE submissions ADD COLUMN case_results TEXT NOT NULL DEFAULT '[]';
ALTER TABLE contests ADD COLUMN config TEXT NOT NULL DEFAULT '{}';
ALTER TABLE contests ADD COLUMN deleted_at TEXT;
