-- Immutable private chunks. the legacy snapshot remains an intact recovery copy.
CREATE TABLE IF NOT EXISTS account_chunk_heads (
 user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 revision BIGINT NOT NULL,
 root_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 previous_root CHAR(64) CHARACTER SET ascii COLLATE ascii_bin,
 updated_at VARCHAR(30) NOT NULL,
 CONSTRAINT chunk_head_account FOREIGN KEY(user_id) REFERENCES accounts(user_id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS account_chunk_usage (
 user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 byte_count BIGINT NOT NULL DEFAULT 0,
 object_count INT NOT NULL DEFAULT 0,
 last_gc_at VARCHAR(30) NOT NULL DEFAULT '',
 CONSTRAINT chunk_usage_account FOREIGN KEY(user_id) REFERENCES accounts(user_id)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS account_chunks (
 user_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 kind VARCHAR(8) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 payload MEDIUMBLOB NOT NULL,
 children TEXT CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 byte_count INT NOT NULL,
 created_at VARCHAR(30) NOT NULL,
 seen_at VARCHAR(30) NOT NULL,
 PRIMARY KEY(user_id,hash),
 INDEX chunk_age(user_id,seen_at),
 CONSTRAINT chunk_owner FOREIGN KEY(user_id) REFERENCES accounts(user_id)
) ENGINE=InnoDB;
