CREATE TABLE IF NOT EXISTS visa_registrations (
    id BIGSERIAL PRIMARY KEY,
    application_code VARCHAR(64) UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    passport_number VARCHAR(64) NOT NULL,
    visa_type VARCHAR(32) NOT NULL DEFAULT '',
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_visa_registrations_passport_number
    ON visa_registrations (passport_number);

CREATE INDEX IF NOT EXISTS idx_visa_registrations_status
    ON visa_registrations (status);
