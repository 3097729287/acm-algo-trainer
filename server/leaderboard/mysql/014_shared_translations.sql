CREATE TABLE IF NOT EXISTS shared_statement_translations (
  translation_key CHAR(64) CHARACTER SET ascii PRIMARY KEY,
  source_url VARCHAR(2048) NOT NULL,
  source_hash CHAR(64) CHARACTER SET ascii NOT NULL,
  source_format VARCHAR(40) CHARACTER SET ascii NOT NULL,
  target_language VARCHAR(10) CHARACTER SET ascii NOT NULL,
  markdown MEDIUMTEXT NOT NULL,
  contributor_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
  created_at CHAR(24) CHARACTER SET ascii NOT NULL,
  FOREIGN KEY(contributor_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin;
