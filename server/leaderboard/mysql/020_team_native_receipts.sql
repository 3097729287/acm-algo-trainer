-- Verified native attempts supplement first-AC events, including repeated AC.
-- No changes to personal/ranking first-AC events or previously earned rewards.
CREATE TABLE IF NOT EXISTS team_native_receipts(
 receipt_key CHAR(64) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 room_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 problem_id VARCHAR(512) NOT NULL,
 user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin,
 intent_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 verdict VARCHAR(16) NOT NULL, accepted_at VARCHAR(32) NOT NULL,
 verified_at BIGINT NOT NULL, proof TEXT NOT NULL,
 FOREIGN KEY(room_id,problem_id) REFERENCES team_problems(room_id,problem_id),
 FOREIGN KEY(user_id) REFERENCES accounts(user_id) ON DELETE SET NULL,
 UNIQUE KEY team_native_intent(user_id,intent_id),
 INDEX team_verified_score(room_id,verdict,accepted_at)
) ENGINE=InnoDB;
