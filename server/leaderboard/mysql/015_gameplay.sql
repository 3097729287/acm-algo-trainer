-- Additive migration only. No existing account, snapshot or ranking row changes.
CREATE TABLE IF NOT EXISTS gameplay_accounts (
 user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY, payload LONGTEXT NOT NULL,
 FOREIGN KEY(user_id) REFERENCES accounts(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS gameplay_operations (
 user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL, request_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 request_hash CHAR(64) NOT NULL, response LONGTEXT NOT NULL,
 PRIMARY KEY(user_id,request_id), FOREIGN KEY(user_id) REFERENCES accounts(user_id) ON DELETE CASCADE
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS duel_lobby(singleton INT PRIMARY KEY,payload LONGTEXT NOT NULL) ENGINE=InnoDB;
INSERT IGNORE INTO duel_lobby(singleton,payload) VALUES(1,'{"queue":[]}');
CREATE TABLE IF NOT EXISTS duel_matches(match_id CHAR(36) PRIMARY KEY,payload LONGTEXT NOT NULL) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS duel_members(user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,match_id CHAR(36) NOT NULL,
 FOREIGN KEY(user_id) REFERENCES accounts(user_id) ON DELETE CASCADE,
 FOREIGN KEY(match_id) REFERENCES duel_matches(match_id)) ENGINE=InnoDB;
