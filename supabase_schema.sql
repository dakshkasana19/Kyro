-- ============================================================
-- Kyro — TRIAGE-AI  |  Supabase SQL Schema
-- Run this in the Supabase SQL Editor to bootstrap the DB.
-- ============================================================

-- Enable uuid generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- --------------------------------------------------------
-- HOSPITALS (Multi-tenancy)
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS hospitals (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        TEXT        NOT NULL,
    address     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE hospitals IS 'Healthcare facilities (tenants) in the system.';

-- --------------------------------------------------------
-- PROFILES (RBAC & Tenant Link)
-- -------------------
-- Extends auth.users with role and hospital context.
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    hospital_id UUID        NOT NULL REFERENCES hospitals(id),
    role        TEXT        NOT NULL CHECK (role IN ('Admin', 'Doctor', 'Nurse')),
    full_name   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE profiles IS 'User profiles extending authentication with roles and hospital context.';

-- --------------------------------------------------------
-- PATIENTS
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS patients (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hospital_id     UUID        NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    name            TEXT        NOT NULL,
    age             INT         NOT NULL CHECK (age >= 0 AND age <= 150),
    gender          TEXT        NOT NULL CHECK (gender IN ('male', 'female', 'other')),
    symptoms        JSONB       NOT NULL DEFAULT '[]'::jsonb,
    vitals          JSONB       NOT NULL DEFAULT '{}'::jsonb,
    history         JSONB       NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE patients IS 'Patient intake records scoped by hospital.';

CREATE INDEX IF NOT EXISTS idx_patients_hospital ON patients (hospital_id);
CREATE INDEX IF NOT EXISTS idx_patients_created_at ON patients (created_at DESC);

-- --------------------------------------------------------
-- DOCTORS
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS doctors (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hospital_id     UUID        NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    name            TEXT        NOT NULL,
    specialization  TEXT        NOT NULL,
    max_capacity    INT         NOT NULL DEFAULT 10 CHECK (max_capacity > 0),
    current_load    INT         NOT NULL DEFAULT 0  CHECK (current_load >= 0),
    is_available    BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE doctors IS 'Registered doctors scoped by hospital.';

CREATE INDEX IF NOT EXISTS idx_doctors_hospital       ON doctors (hospital_id);
CREATE INDEX IF NOT EXISTS idx_doctors_specialization ON doctors (specialization);
CREATE INDEX IF NOT EXISTS idx_doctors_available      ON doctors (is_available) WHERE is_available = TRUE;

-- --------------------------------------------------------
-- TRIAGE LOGS
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS triage_logs (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hospital_id         UUID        NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    patient_id          UUID        NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    severity_level      INT         NOT NULL CHECK (severity_level BETWEEN 0 AND 3),
    confidence_score    FLOAT       NOT NULL CHECK (confidence_score BETWEEN 0.0 AND 1.0),
    shap_summary        JSONB       NOT NULL DEFAULT '{}'::jsonb,
    assigned_doctor_id  UUID        REFERENCES doctors(id) ON DELETE SET NULL,
    model_version       TEXT        NOT NULL DEFAULT '1.0.0',
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE triage_logs IS 'AI triage results scoped by hospital.';

CREATE INDEX IF NOT EXISTS idx_triage_hospital   ON triage_logs (hospital_id);
CREATE INDEX IF NOT EXISTS idx_triage_severity   ON triage_logs (severity_level);
CREATE INDEX IF NOT EXISTS idx_triage_created_at  ON triage_logs (created_at DESC);

-- --------------------------------------------------------
-- AUDIT LOG
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_log (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hospital_id UUID        REFERENCES hospitals(id) ON DELETE CASCADE,
    actor       TEXT        NOT NULL,
    action      TEXT        NOT NULL,
    resource    TEXT        NOT NULL,
    resource_id UUID,
    metadata    JSONB       DEFAULT '{}'::jsonb,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_hospital   ON audit_log (hospital_id);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_log (created_at DESC);

-- --------------------------------------------------------
-- ROW LEVEL SECURITY (RLS)
-- --------------------------------------------------------

-- Enable RLS
ALTER TABLE hospitals ENABLE ROW LEVEL SECURITY;
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE doctors ENABLE ROW LEVEL SECURITY;
ALTER TABLE triage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Profiles: Users can read all profiles in their hospital, but only update their own.
CREATE POLICY "Profiles are viewable by same hospital members" 
ON profiles FOR SELECT 
USING (hospital_id = (SELECT hospital_id FROM profiles WHERE id = auth.uid()));

CREATE POLICY "Users can update own profile" 
ON profiles FOR UPDATE 
USING (id = auth.uid());

-- Scoped access policies for clinical data
CREATE POLICY "Scoped hospital access: patients" 
ON patients FOR ALL 
USING (hospital_id = (SELECT hospital_id FROM profiles WHERE id = auth.uid()));

CREATE POLICY "Scoped hospital access: doctors" 
ON doctors FOR ALL 
USING (hospital_id = (SELECT hospital_id FROM profiles WHERE id = auth.uid()));

CREATE POLICY "Scoped hospital access: triage_logs" 
ON triage_logs FOR ALL 
USING (hospital_id = (SELECT hospital_id FROM profiles WHERE id = auth.uid()));

-- --------------------------------------------------------
-- SEEDING
-- --------------------------------------------------------
-- Create initial hospital
INSERT INTO hospitals (id, name, address) 
VALUES ('f47ac10b-58cc-4372-a567-0e02b2c3d479', 'Kyro Central Clinic', '77 Health Ave, Silicon Valley')
ON CONFLICT (id) DO NOTHING;

-- --------------------------------------------------------
-- PROFILE AUTOMATION
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, hospital_id, role, full_name)
    VALUES (
        NEW.id,
        COALESCE((NEW.raw_user_meta_data->>'hospital_id')::uuid, 'f47ac10b-58cc-4372-a567-0e02b2c3d479'),
        COALESCE(NEW.raw_user_meta_data->>'role', 'Nurse'),
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'System User')
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- --------------------------------------------------------
-- UPDATED_AT TRIGGER
-- --------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_profiles_updated_at BEFORE UPDATE ON profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_patients_updated_at BEFORE UPDATE ON patients FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER trg_doctors_updated_at BEFORE UPDATE ON doctors FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
