CREATE TABLE IF NOT EXISTS account_public_avatars (
  user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  data MEDIUMTEXT CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  updated_at VARCHAR(30) NOT NULL,
  CONSTRAINT public_avatar_account FOREIGN KEY(user_id) REFERENCES accounts(user_id)
) ENGINE=InnoDB;
