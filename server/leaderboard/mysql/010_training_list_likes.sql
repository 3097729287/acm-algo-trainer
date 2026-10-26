CREATE TABLE IF NOT EXISTS training_list_likes (
  actor_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  list_id VARCHAR(160) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL,
  liked_day VARCHAR(10) NOT NULL,
  created_at VARCHAR(30) NOT NULL,
  PRIMARY KEY(actor_id,list_id,liked_day),
  INDEX training_list_totals(list_id,liked_day),
  CONSTRAINT training_list_like_actor FOREIGN KEY(actor_id) REFERENCES users(user_id)
) ENGINE=InnoDB;
