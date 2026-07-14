CREATE TABLE "schema_migrations" (version varchar(128) primary key);
CREATE TABLE fields (
    id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL UNIQUE,
    keywords TEXT NOT NULL,
    PRIMARY KEY (id)
);
CREATE TABLE institutions (
    id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
);
CREATE TABLE researches (
    id VARCHAR(36) NOT NULL,
    data_id INT NULL,
    title VARCHAR(255) NOT NULL,
    abstract TEXT NULL,
    year INT NOT NULL,

    field_id VARCHAR(36) NULL,
    unit VARCHAR(255) NULL,
    cluster VARCHAR(255) NULL,
    contribution_category VARCHAR(40) NULL, -- this column to categorize is it [research, commiunity_service]

    start_at DATE NULL,
    finish_at DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (id),
    FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE SET NULL
);
CREATE INDEX idx_researches_year ON researches(year);
CREATE TABLE authors (
    id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    nidn VARCHAR(255) NULL,
    PRIMARY KEY (id)
);
CREATE TABLE research_authors (
    research_id VARCHAR(36) NOT NULL,
    author_id VARCHAR(36) NOT NULL,
    role VARCHAR(128) NULL,
    PRIMARY KEY (research_id, author_id),
    FOREIGN KEY (research_id) REFERENCES researches(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
);
CREATE TABLE research_institutions (
    research_id VARCHAR(36) NOT NULL,
    institution_id VARCHAR(36) NOT NULL,
    PRIMARY KEY (research_id, institution_id),
    FOREIGN KEY (research_id) REFERENCES researches(id) ON DELETE CASCADE,
    FOREIGN KEY (institution_id) REFERENCES institutions(id) ON DELETE CASCADE
);
CREATE TABLE research_validation_flags (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    research_id VARCHAR(36) NOT NULL UNIQUE REFERENCES researches(id) ON DELETE CASCADE,

    is_entropy BOOLEAN DEFAULT FALSE,
    category VARCHAR(128),
    status VARCHAR(32),
    confidence_score FLOAT,
    alt_category VARCHAR(128),
    alt_score FLOAT,
    gap FLOAT,
    reason TEXT,
    is_efficiency VARCHAR(8),
    efficiency_score FLOAT,
    model_version VARCHAR(16),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_validation_entropy ON research_validation_flags(is_entropy);
CREATE TABLE categorization_config (
    `key` VARCHAR(64) NOT NULL PRIMARY KEY,
    `value` FLOAT NOT NULL,
    `description` VARCHAR(255) NULL
);
CREATE TABLE efficiency_keyword_groups (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    group_order INT NOT NULL UNIQUE,
    label VARCHAR(128) NOT NULL
);
CREATE TABLE efficiency_keywords (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    group_id VARCHAR(36) NOT NULL,
    keyword VARCHAR(255) NOT NULL,
    language VARCHAR(8) DEFAULT 'EN' NOT NULL,
    FOREIGN KEY (group_id) REFERENCES efficiency_keyword_groups(id) ON DELETE CASCADE
);
CREATE INDEX idx_efficiency_keywords_group ON efficiency_keywords(group_id);
CREATE TABLE efficiency_cue_words (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    word VARCHAR(128) NOT NULL UNIQUE
);
-- Dbmate schema migrations
INSERT INTO "schema_migrations" (version) VALUES
  ('20260602051406');
