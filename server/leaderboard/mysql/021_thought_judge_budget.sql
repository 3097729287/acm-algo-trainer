-- Additive, idempotent provider-call budget. Keep counters on rollback/restart.
-- usage_day follows the Beijing day, pk_lobby serializes all reservations.
CREATE TABLE IF NOT EXISTS pk_judge_usage(
 usage_day DATE PRIMARY KEY,
 calls INT NOT NULL DEFAULT 0
) ENGINE=InnoDB;
