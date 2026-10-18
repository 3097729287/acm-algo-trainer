CREATE TABLE IF NOT EXISTS account_nicknames (
  nickname_key CHAR(64) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,
  CONSTRAINT account_nickname_user FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;

-- Existing deployments must also run scripts/migrate-nicknames.mjs while API is
-- stopped. It preflights Unicode-normalized names before reserving any of them.
