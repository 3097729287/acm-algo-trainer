CREATE TABLE IF NOT EXISTS accounts (
  user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  login_id VARCHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,
  password_hash VARCHAR(200) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  password_version INT NOT NULL DEFAULT 1,
  created_at VARCHAR(30) NOT NULL,
  updated_at VARCHAR(30) NOT NULL,
  CONSTRAINT accounts_user FOREIGN KEY(user_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS account_sessions (
  token_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  password_version INT NOT NULL,
  expires_at BIGINT NOT NULL,
  created_at VARCHAR(30) NOT NULL,
  INDEX sessions_user(user_id),
  INDEX sessions_expiry(expires_at),
  CONSTRAINT sessions_account FOREIGN KEY(user_id) REFERENCES accounts(user_id)
) ENGINE=InnoDB;
