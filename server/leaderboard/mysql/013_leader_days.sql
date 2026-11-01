CREATE TABLE IF NOT EXISTS ranking_leader_schedule (
  singleton TINYINT PRIMARY KEY,
  next_day CHAR(10) CHARACTER SET ascii NOT NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS ranking_leader_days (
  period VARCHAR(8) CHARACTER SET ascii NOT NULL,
  ranking_day CHAR(10) CHARACTER SET ascii NOT NULL,
  user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  score INTEGER NOT NULL,
  observed_at CHAR(24) CHARACTER SET ascii NOT NULL,
  PRIMARY KEY(period,ranking_day),
  KEY ranking_leader_owner(user_id,period,ranking_day),
  FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;
