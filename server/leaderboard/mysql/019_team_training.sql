-- Additive only. Retain shared drafts and historical rooms when rolling back.
CREATE TABLE IF NOT EXISTS team_lobby(singleton INT PRIMARY KEY) ENGINE=InnoDB;
INSERT IGNORE INTO team_lobby(singleton) VALUES(1);
CREATE TABLE IF NOT EXISTS teams(
 team_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 invite_code CHAR(8) CHARACTER SET ascii COLLATE ascii_bin NOT NULL UNIQUE,
 archived TINYINT NOT NULL DEFAULT 0, payload MEDIUMTEXT NOT NULL
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS team_members(
 user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 team_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 ready TINYINT NOT NULL DEFAULT 0, last_seen BIGINT NOT NULL, joined_at BIGINT NOT NULL,
 FOREIGN KEY(user_id) REFERENCES accounts(user_id) ON DELETE CASCADE,
 FOREIGN KEY(team_id) REFERENCES teams(team_id), INDEX team_roster(team_id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS team_rooms(
 room_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 team_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 status VARCHAR(16) NOT NULL, started_at VARCHAR(32) NOT NULL, deadline BIGINT NOT NULL,
 ended_at VARCHAR(32) NOT NULL, updated_at BIGINT NOT NULL, payload MEDIUMTEXT NOT NULL,
 FOREIGN KEY(team_id) REFERENCES teams(team_id), INDEX team_room_history(team_id,updated_at)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS team_room_members(
 room_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 PRIMARY KEY(room_id,user_id),
 FOREIGN KEY(room_id) REFERENCES team_rooms(room_id),
 FOREIGN KEY(user_id) REFERENCES accounts(user_id) ON DELETE CASCADE,
 INDEX team_member_history(user_id,room_id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS team_problems(
 room_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 problem_id VARCHAR(512) NOT NULL, problem_key CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 available TINYINT NOT NULL, PRIMARY KEY(room_id,problem_id),
 FOREIGN KEY(room_id) REFERENCES team_rooms(room_id), INDEX team_problem_identity(room_id,problem_key)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS team_drafts(
 room_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 problem_id VARCHAR(512) NOT NULL, language VARCHAR(16) NOT NULL, code MEDIUMTEXT NOT NULL,
 revision INT NOT NULL, edited_by VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
 updated_at BIGINT NOT NULL, PRIMARY KEY(room_id,problem_id),
 FOREIGN KEY(room_id,problem_id) REFERENCES team_problems(room_id,problem_id),
 FOREIGN KEY(edited_by) REFERENCES accounts(user_id) ON DELETE SET NULL
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS team_operations(
 user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 request_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 request_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 ack TEXT NOT NULL, created_at BIGINT NOT NULL, PRIMARY KEY(user_id,request_id),
 FOREIGN KEY(user_id) REFERENCES accounts(user_id) ON DELETE CASCADE,
 INDEX team_operation_age(created_at)
) ENGINE=InnoDB;
