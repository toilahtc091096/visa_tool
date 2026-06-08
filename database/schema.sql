CREATE TABLE IF NOT EXISTS visa_registrations (
    id BIGSERIAL PRIMARY KEY,
    first_applyid VARCHAR(64),
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

CREATE UNIQUE INDEX IF NOT EXISTS uq_visa_registrations_first_applyid
    ON visa_registrations (first_applyid);

CREATE INDEX IF NOT EXISTS idx_visa_registrations_passport_number
    ON visa_registrations (passport_number);

CREATE INDEX IF NOT EXISTS idx_visa_registrations_status
    ON visa_registrations (status);
