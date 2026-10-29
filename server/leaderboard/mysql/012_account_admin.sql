-- Maintenance audit has no user FK so deleted targets remain auditable.
-- Passwords, hashes and reset secrets never enter this table.
CREATE TABLE IF NOT EXISTS account_admin_actions (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 actor_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 target_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 action VARCHAR(24) CHARACTER SET ascii NOT NULL,
 created_at VARCHAR(30) NOT NULL,
 INDEX account_admin_actor(actor_id,created_at),
 INDEX account_admin_target(target_id,created_at)
) ENGINE=InnoDB;
