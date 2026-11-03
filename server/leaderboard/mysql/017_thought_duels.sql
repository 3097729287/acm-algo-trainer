-- Additive and idempotent. Disable both PK switches before rolling back code.
-- Keep pk_* tables when rolling back so submissions and records remain intact.
CREATE TABLE IF NOT EXISTS pk_lobby(singleton INT PRIMARY KEY) ENGINE=InnoDB;
INSERT IGNORE INTO pk_lobby(singleton) VALUES(1);
CREATE TABLE IF NOT EXISTS pk_ratings(
 user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 rating INT NOT NULL DEFAULT 1000,
 FOREIGN KEY(user_id) REFERENCES accounts(user_id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS pk_queue(
 user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 ticket CHAR(36) NOT NULL, rating INT NOT NULL, joined_at BIGINT NOT NULL,
 last_seen BIGINT NOT NULL, min_difficulty INT NOT NULL, max_difficulty INT NOT NULL,
 FOREIGN KEY(user_id) REFERENCES accounts(user_id), INDEX pk_queue_age(joined_at)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS pk_matches(
 match_id CHAR(36) PRIMARY KEY, status VARCHAR(16) NOT NULL,
 updated_at BIGINT NOT NULL, due_at BIGINT NOT NULL, payload MEDIUMTEXT NOT NULL,
 INDEX pk_match_status(status,due_at)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS pk_members(
 user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 match_id CHAR(36) NOT NULL,
 FOREIGN KEY(user_id) REFERENCES accounts(user_id),
 FOREIGN KEY(match_id) REFERENCES pk_matches(match_id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS pk_records(
 match_id CHAR(36) PRIMARY KEY, player_a VARCHAR(36) NOT NULL,
 player_b VARCHAR(36) NOT NULL, finished_at BIGINT NOT NULL, payload MEDIUMTEXT NOT NULL,
 FOREIGN KEY(match_id) REFERENCES pk_matches(match_id),
 INDEX pk_record_a(player_a,finished_at), INDEX pk_record_b(player_b,finished_at)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS pk_operations(
 user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 request_id CHAR(36) NOT NULL, request_hash CHAR(64) NOT NULL,
 PRIMARY KEY(user_id,request_id), FOREIGN KEY(user_id) REFERENCES accounts(user_id)
) ENGINE=InnoDB;
