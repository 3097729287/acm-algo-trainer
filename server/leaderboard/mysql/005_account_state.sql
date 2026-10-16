CREATE TABLE IF NOT EXISTS account_state (
  user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  revision BIGINT NOT NULL DEFAULT 0,
  payload MEDIUMTEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  updated_at VARCHAR(30) NOT NULL,
  CONSTRAINT state_account FOREIGN KEY(user_id) REFERENCES accounts(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS account_login_days (
  user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  day CHAR(10) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  first_seen_at VARCHAR(30) NOT NULL,
  PRIMARY KEY(user_id,day),
  INDEX login_days_day(day,user_id),
  CONSTRAINT login_days_account FOREIGN KEY(user_id) REFERENCES accounts(user_id)
) ENGINE=InnoDB;
