-- Additive only. Historical AC/XP, prior match outcomes and opened packs remain.
CREATE TABLE IF NOT EXISTS account_presence(
 user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 token_hash CHAR(64) NOT NULL, activity VARCHAR(20) NOT NULL, last_seen BIGINT NOT NULL,
 FOREIGN KEY(user_id) REFERENCES accounts(user_id) ON DELETE CASCADE,
 INDEX presence_age(last_seen)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS ranked_duel_ratings(
 user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 rating INT NOT NULL DEFAULT 1000, games INT NOT NULL DEFAULT 0,
 wins INT NOT NULL DEFAULT 0, updated_at BIGINT NOT NULL,
 FOREIGN KEY(user_id) REFERENCES accounts(user_id) ON DELETE CASCADE,
 INDEX ranked_points(rating,user_id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS ranked_duel_records(
 match_id CHAR(36) PRIMARY KEY, finished_at BIGINT NOT NULL, payload MEDIUMTEXT NOT NULL,
 FOREIGN KEY(match_id) REFERENCES duel_matches(match_id), INDEX ranked_today(finished_at,match_id)
) ENGINE=InnoDB;
