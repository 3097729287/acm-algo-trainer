CREATE TABLE IF NOT EXISTS social_likes (
  actor_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  recipient_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  liked_day VARCHAR(10) NOT NULL,
  created_at VARCHAR(30) NOT NULL,
  PRIMARY KEY(actor_id,recipient_id,liked_day),
  INDEX social_likes_recipient(recipient_id,liked_day),
  CONSTRAINT social_like_actor FOREIGN KEY(actor_id) REFERENCES users(user_id),
  CONSTRAINT social_like_recipient FOREIGN KEY(recipient_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS social_notifications (
  id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
  kind VARCHAR(12) NOT NULL,
  actor_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  recipient_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  body VARCHAR(2000) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL DEFAULT '',
  created_at VARCHAR(30) NOT NULL,
  read_at VARCHAR(30) NULL,
  INDEX social_inbox(recipient_id,created_at),
  INDEX social_activity(kind,created_at),
  CONSTRAINT social_notice_actor FOREIGN KEY(actor_id) REFERENCES users(user_id),
  CONSTRAINT social_notice_recipient FOREIGN KEY(recipient_id) REFERENCES users(user_id)
) ENGINE=InnoDB;
