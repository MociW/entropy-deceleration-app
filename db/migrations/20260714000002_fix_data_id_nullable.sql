-- migrate:up
-- Align data_id to nullable — the original schema had NOT NULL but the application
-- already handles NULL data_id values (see categorizer.py save_to_db). This migration
-- corrects the schema to reflect actual intent.
--
-- SQLite does not support ALTER COLUMN; we recreate the table.
-- For MySQL/PostgreSQL use:
--   ALTER TABLE researches MODIFY data_id INT NULL;

CREATE TABLE researches_new (
    id VARCHAR(36) NOT NULL,
    data_id INT NULL,                       -- was NOT NULL, corrected to NULL
    title VARCHAR(255) NOT NULL,
    abstract TEXT NULL,
    year INT NOT NULL,
    field_id VARCHAR(36) NULL,
    unit VARCHAR(255) NULL,
    cluster VARCHAR(255) NULL,
    contribution_category VARCHAR(40) NULL,
    start_at DATE NULL,
    finish_at DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE SET NULL
);

INSERT INTO researches_new SELECT * FROM researches;
DROP TABLE researches;
ALTER TABLE researches_new RENAME TO researches;
CREATE INDEX IF NOT EXISTS idx_researches_year ON researches(year);

INSERT INTO schema_migrations (version) VALUES ('20260714000002');

-- migrate:down
-- Reverting to NOT NULL would fail if any NULL data_id rows exist. Intentionally left
-- as a no-op to prevent accidental data loss.
DELETE FROM schema_migrations WHERE version = '20260714000002';
