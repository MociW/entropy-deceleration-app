-- migrate:up
-- SQLite does not support ALTER COLUMN; this trigger replicates onupdate behaviour
-- for research_validation_flags.updated_at.
-- For MySQL/PostgreSQL deployments, replace with:
--   ALTER TABLE research_validation_flags
--     MODIFY updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP;

CREATE TRIGGER IF NOT EXISTS trg_validation_flags_updated_at
AFTER UPDATE ON research_validation_flags
FOR EACH ROW
BEGIN
    UPDATE research_validation_flags
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = OLD.id;
END;

INSERT INTO schema_migrations (version) VALUES ('20260714000001');

-- migrate:down
DROP TRIGGER IF EXISTS trg_validation_flags_updated_at;
DELETE FROM schema_migrations WHERE version = '20260714000001';
