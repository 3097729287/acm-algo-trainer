CREATE TABLE IF NOT EXISTS ranking_admins (
  user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  granted_at CHAR(24) CHARACTER SET ascii NOT NULL,
  FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

CREATE TABLE IF NOT EXISTS ranking_exclusions (
  user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  problem_key CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  deleted_at CHAR(24) CHARACTER SET ascii NOT NULL,
  PRIMARY KEY (user_id,problem_key),
  FOREIGN KEY (user_id,problem_key) REFERENCES official_ac_events(user_id,problem_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

CREATE TABLE IF NOT EXISTS ranking_schedule (
  singleton TINYINT PRIMARY KEY,
  daily_start CHAR(10) CHARACTER SET ascii NOT NULL,
  weekly_start CHAR(10) CHARACTER SET ascii NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ranking_cycles (
  period VARCHAR(8) CHARACTER SET ascii NOT NULL,
  start_date CHAR(10) CHARACTER SET ascii NOT NULL,
  end_date CHAR(10) CHARACTER SET ascii NOT NULL,
  settled_at CHAR(24) CHARACTER SET ascii NOT NULL,
  PRIMARY KEY (period,start_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ranking_rewards (
  user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  period VARCHAR(8) CHARACTER SET ascii NOT NULL,
  start_date CHAR(10) CHARACTER SET ascii NOT NULL,
  end_date CHAR(10) CHARACTER SET ascii NOT NULL,
  position TINYINT NOT NULL,
  xp INTEGER NOT NULL,
  settled_at CHAR(24) CHARACTER SET ascii NOT NULL,
  PRIMARY KEY (user_id,period,start_date),
  FOREIGN KEY (user_id) REFERENCES users(user_id),
  FOREIGN KEY (period,start_date) REFERENCES ranking_cycles(period,start_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ranking_admin_actions (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  actor_id VARCHAR(36) CHARACTER SET ascii NOT NULL,
  target_id VARCHAR(36) CHARACTER SET ascii,
  period VARCHAR(8) CHARACTER SET ascii NOT NULL,
  start_date CHAR(10) CHARACTER SET ascii,
  end_date CHAR(10) CHARACTER SET ascii,
  removed_count INTEGER NOT NULL,
  created_at CHAR(24) CHARACTER SET ascii NOT NULL
) ENGINE=InnoDB;
