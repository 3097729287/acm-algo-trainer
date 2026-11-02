-- New optional message metadata. Existing inbox rows and bodies stay intact.
CREATE TABLE IF NOT EXISTS social_comment_details (
 message_id VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin PRIMARY KEY,
 reply_to VARCHAR(36) CHARACTER SET ascii COLLATE ascii_bin NULL,
 request_hash CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 gift_payload TEXT NULL,
 INDEX social_reply_parent(reply_to),
 FOREIGN KEY(message_id) REFERENCES social_notifications(id) ON DELETE CASCADE,
 FOREIGN KEY(reply_to) REFERENCES social_notifications(id) ON DELETE SET NULL
) ENGINE=InnoDB;
