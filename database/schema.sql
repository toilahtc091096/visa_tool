CREATE TABLE IF NOT EXISTS visa_registrations (
    id BIGSERIAL PRIMARY KEY,
    first_applyid VARCHAR(64),
    application_code VARCHAR(64) NOT NULL DEFAULT '',
    full_name VARCHAR(255) NOT NULL,
    passport_number VARCHAR(64) NOT NULL,
    visa_type VARCHAR(32) NOT NULL DEFAULT '',
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE visa_registrations
    ADD COLUMN IF NOT EXISTS first_applyid VARCHAR(64);

ALTER TABLE visa_registrations
    ADD COLUMN IF NOT EXISTS application_code VARCHAR(64) NOT NULL DEFAULT '';

ALTER TABLE visa_registrations
    DROP CONSTRAINT IF EXISTS visa_registrations_application_code_key;

DROP INDEX IF EXISTS visa_registrations_application_code_key;

CREATE UNIQUE INDEX IF NOT EXISTS uq_visa_registrations_first_applyid
    ON visa_registrations (first_applyid);

CREATE UNIQUE INDEX IF NOT EXISTS uq_visa_registrations_application_code_not_blank
    ON visa_registrations (application_code)
    WHERE application_code <> '';

CREATE INDEX IF NOT EXISTS idx_visa_registrations_passport_number
    ON visa_registrations (passport_number);

CREATE INDEX IF NOT EXISTS idx_visa_registrations_status
    ON visa_registrations (status);

CREATE TABLE IF NOT EXISTS han_approval_jobs (
    id BIGSERIAL PRIMARY KEY,
    han_code VARCHAR(64) NOT NULL UNIQUE,
    source_email VARCHAR(255) NOT NULL DEFAULT '',
    message_id VARCHAR(255) NOT NULL DEFAULT '',
    subject VARCHAR(512) NOT NULL DEFAULT '',
    status VARCHAR(32) NOT NULL DEFAULT 'not_print',
    attachment_paths JSONB NOT NULL DEFAULT '[]'::jsonb,
    application_form_path VARCHAR(512) NOT NULL DEFAULT '',
    attempt_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT NOT NULL DEFAULT '',
    printed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_han_approval_jobs_status
    ON han_approval_jobs (status);

CREATE INDEX IF NOT EXISTS idx_han_approval_jobs_han_code
    ON han_approval_jobs (han_code);

-- Agencies (đại lý gốc). Shared by both regions: MB = every North record,
-- CHUNG = South records sent without an agency code.
CREATE TABLE IF NOT EXISTS agencies (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(64) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- MB and CHUNG are created per house by init_database (database/connection.py).

-- Old records keep agency_id NULL.
ALTER TABLE visa_registrations
    ADD COLUMN IF NOT EXISTS agency_id BIGINT REFERENCES agencies (id);

CREATE INDEX IF NOT EXISTS idx_visa_registrations_agency_id
    ON visa_registrations (agency_id);

-- skip = TRUE: the South sync ignores the record. Added once: every record
-- already in the table at that moment (old, no agency) is marked skip.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'visa_registrations' AND column_name = 'skip'
    ) THEN
        ALTER TABLE visa_registrations
            ADD COLUMN skip BOOLEAN NOT NULL DEFAULT FALSE;
        UPDATE visa_registrations SET skip = TRUE;
    END IF;
END $$;

-- VIP registration (is_vip = 1 in the /run curl, from source_prefix "... - vip").
ALTER TABLE visa_registrations
    ADD COLUMN IF NOT EXISTS is_vip BOOLEAN NOT NULL DEFAULT FALSE;

-- Web input form (/web): one account per person (staff code BAO, HANG, LONG, ADMIN).
-- password_hash = "pbkdf2_sha256$<iterations>$<salt hex>$<hash hex>"; api_key is the
-- person's own key, returned at login and sent back as X-Api-Key by the page.
CREATE TABLE IF NOT EXISTS web_users (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    staff_code TEXT NOT NULL,
    api_key TEXT NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Runs started from /web, with the progress steps n8n reports back (POST /web/progress).
-- steps = [{"step": "files_loaded", "label": "...", "message": "...", "at": "<iso>"}, ...]
CREATE TABLE IF NOT EXISTS web_jobs (
    job_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    staff_code TEXT NOT NULL,
    house TEXT NOT NULL,
    visa_type TEXT NOT NULL,
    source_prefix TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    message TEXT NOT NULL DEFAULT '',
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_web_jobs_username_started ON web_jobs (username, started_at DESC);

-- The curl WF-13 built (sent by n8n with the "done" step); the page loads it into the curl tab.
ALTER TABLE web_jobs ADD COLUMN IF NOT EXISTS curl TEXT NOT NULL DEFAULT '';

-- One database for every house (HAI, PHONG, TAI). Each row carries its house;
-- database/crud filters on the instance's house (database/house.py).
-- staff_code / job_id: who started the record (first /run that created it).
ALTER TABLE visa_registrations ADD COLUMN IF NOT EXISTS house TEXT NOT NULL DEFAULT '';
ALTER TABLE visa_registrations ADD COLUMN IF NOT EXISTS staff_code TEXT NOT NULL DEFAULT '';
ALTER TABLE visa_registrations ADD COLUMN IF NOT EXISTS job_id TEXT NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_visa_registrations_house_created ON visa_registrations (house, created_at);
CREATE INDEX IF NOT EXISTS idx_visa_registrations_staff_created ON visa_registrations (staff_code, created_at);

ALTER TABLE han_approval_jobs ADD COLUMN IF NOT EXISTS house TEXT NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_han_approval_jobs_house ON han_approval_jobs (house);

-- Agencies are per house (only the South house really uses them): code is unique per house.
ALTER TABLE agencies ADD COLUMN IF NOT EXISTS house TEXT NOT NULL DEFAULT '';
ALTER TABLE agencies DROP CONSTRAINT IF EXISTS agencies_code_key;
CREATE UNIQUE INDEX IF NOT EXISTS uq_agencies_house_code ON agencies (house, code);
