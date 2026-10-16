CREATE TABLE IF NOT EXISTS account_public_progress (
  user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  payload VARCHAR(4096) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  updated_at VARCHAR(30) NOT NULL,
  CONSTRAINT public_progress_account FOREIGN KEY(user_id) REFERENCES accounts(user_id)
) ENGINE=InnoDB;
