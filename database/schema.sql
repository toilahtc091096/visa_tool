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

CREATE UNIQUE INDEX IF NOT EXISTS uq_visa_registrations_first_applyid
    ON visa_registrations (first_applyid);

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
