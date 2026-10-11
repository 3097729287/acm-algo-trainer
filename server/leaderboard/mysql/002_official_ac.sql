CREATE TABLE IF NOT EXISTS official_ac_events (
  user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  problem_key CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  event_id CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  accepted_at CHAR(24) CHARACTER SET ascii NOT NULL,
  accepted_day CHAR(10) CHARACTER SET ascii NOT NULL,
  difficulty DOUBLE,
  received_at CHAR(24) CHARACTER SET ascii NOT NULL,
  PRIMARY KEY (user_id, problem_key),
  UNIQUE KEY official_ac_events_event (user_id, event_id),
  KEY official_ac_events_day_user (accepted_day, user_id),
  CONSTRAINT official_ac_events_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
