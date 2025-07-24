-- Clinical NLQ AI Assistant Database Schema
-- PostgreSQL 17+ Compatible Schema for Synthea Clinical Data

-- Create the clinical_data schema
CREATE SCHEMA IF NOT EXISTS clinical_data;

-- Set search path to include our schema
SET search_path TO clinical_data, public;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- CORE PATIENT TABLES
-- =====================================================

-- Patients table (based on Synthea patients.csv structure)
CREATE TABLE clinical_data.patients (
    id UUID PRIMARY KEY,
    birth_date DATE NOT NULL,
    death_date DATE,
    ssn VARCHAR(11),
    drivers VARCHAR(20),
    passport VARCHAR(20),
    prefix VARCHAR(10),
    first_name VARCHAR(50),
    middle_name VARCHAR(50),
    last_name VARCHAR(50),
    suffix VARCHAR(10),
    maiden_name VARCHAR(50),
    marital_status VARCHAR(1),
    race VARCHAR(50),
    ethnicity VARCHAR(50),
    gender VARCHAR(1) NOT NULL,
    birth_place VARCHAR(200),
    address VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    county VARCHAR(100),
    fips VARCHAR(10),
    zip VARCHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    healthcare_expenses DECIMAL(12, 2),
    healthcare_coverage DECIMAL(12, 2),
    income DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Organizations table (healthcare providers/hospitals)
CREATE TABLE clinical_data.organizations (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    address VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    phone VARCHAR(20),
    revenue DECIMAL(15, 2),
    utilization INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Providers table (doctors, nurses, etc.)
CREATE TABLE clinical_data.providers (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES clinical_data.organizations(id),
    name VARCHAR(200) NOT NULL,
    gender VARCHAR(1),
    speciality VARCHAR(100),
    address VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(10),
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    utilization INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payers table (insurance companies)
CREATE TABLE clinical_data.payers (
    id UUID PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    ownership VARCHAR(50),
    address VARCHAR(200),
    city VARCHAR(100),
    state VARCHAR(50),
    zip VARCHAR(10),
    phone VARCHAR(20),
    amount_covered DECIMAL(15, 2),
    amount_uncovered DECIMAL(15, 2),
    revenue DECIMAL(15, 2),
    covered_encounters INTEGER,
    uncovered_encounters INTEGER,
    covered_medications INTEGER,
    uncovered_medications INTEGER,
    covered_procedures INTEGER,
    uncovered_procedures INTEGER,
    covered_immunizations INTEGER,
    uncovered_immunizations INTEGER,
    unique_customers INTEGER,
    qols_avg DECIMAL(5, 3),
    member_months INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- CLINICAL ENCOUNTER TABLES
-- =====================================================

-- Encounters table (visits, admissions, etc.)
CREATE TABLE clinical_data.encounters (
    id UUID PRIMARY KEY,
    start_time TIMESTAMP NOT NULL,
    stop_time TIMESTAMP,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    organization_id UUID REFERENCES clinical_data.organizations(id),
    provider_id UUID REFERENCES clinical_data.providers(id),
    payer_id UUID REFERENCES clinical_data.payers(id),
    encounter_class VARCHAR(50),
    code VARCHAR(20),
    description TEXT,
    base_encounter_cost DECIMAL(10, 2),
    total_claim_cost DECIMAL(10, 2),
    payer_coverage DECIMAL(10, 2),
    reason_code VARCHAR(20),
    reason_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conditions table (diagnoses, problems)
CREATE TABLE clinical_data.conditions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    start_date DATE NOT NULL,
    stop_date DATE,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    encounter_id UUID REFERENCES clinical_data.encounters(id),
    system VARCHAR(50) NOT NULL,
    code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Medications table
CREATE TABLE clinical_data.medications (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    start_date DATE NOT NULL,
    stop_date DATE,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    payer_id UUID REFERENCES clinical_data.payers(id),
    encounter_id UUID REFERENCES clinical_data.encounters(id),
    code VARCHAR(20),
    description TEXT NOT NULL,
    base_cost DECIMAL(10, 2),
    payer_coverage DECIMAL(10, 2),
    dispenses INTEGER,
    total_cost DECIMAL(10, 2),
    reason_code VARCHAR(20),
    reason_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Procedures table
CREATE TABLE clinical_data.procedures (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    date DATE NOT NULL,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    encounter_id UUID REFERENCES clinical_data.encounters(id),
    system VARCHAR(50),
    code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    base_cost DECIMAL(10, 2),
    reason_code VARCHAR(20),
    reason_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Observations table (lab results, vital signs, etc.)
CREATE TABLE clinical_data.observations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    date DATE NOT NULL,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    encounter_id UUID REFERENCES clinical_data.encounters(id),
    category VARCHAR(100),
    system VARCHAR(50),
    code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    value VARCHAR(200),
    units VARCHAR(50),
    type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Immunizations table
CREATE TABLE clinical_data.immunizations (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    date DATE NOT NULL,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    encounter_id UUID REFERENCES clinical_data.encounters(id),
    code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    base_cost DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Allergies table
CREATE TABLE clinical_data.allergies (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    start_date DATE NOT NULL,
    stop_date DATE,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    encounter_id UUID REFERENCES clinical_data.encounters(id),
    system VARCHAR(50),
    code VARCHAR(20) NOT NULL,
    category VARCHAR(100),
    reaction1 VARCHAR(200),
    description1 TEXT,
    severity1 VARCHAR(50),
    reaction2 VARCHAR(200),
    description2 TEXT,
    severity2 VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Care Plans table
CREATE TABLE clinical_data.care_plans (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    start_date DATE NOT NULL,
    stop_date DATE,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    encounter_id UUID REFERENCES clinical_data.encounters(id),
    system VARCHAR(50),
    code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    reason_code VARCHAR(20),
    reason_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- SUPPORTING TABLES
-- =====================================================

-- Devices table (medical devices, equipment)
CREATE TABLE clinical_data.devices (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    start_date DATE NOT NULL,
    stop_date DATE,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    encounter_id UUID REFERENCES clinical_data.encounters(id),
    system VARCHAR(50),
    code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    udi VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Supplies table (medical supplies)
CREATE TABLE clinical_data.supplies (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    date DATE NOT NULL,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    encounter_id UUID REFERENCES clinical_data.encounters(id),
    system VARCHAR(50),
    code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    quantity INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Imaging Studies table
CREATE TABLE clinical_data.imaging_studies (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    date DATE NOT NULL,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    encounter_id UUID REFERENCES clinical_data.encounters(id),
    series_uid VARCHAR(200) NOT NULL,
    body_site_code VARCHAR(20),
    body_site_description TEXT,
    modality_code VARCHAR(20),
    modality_description TEXT,
    instance_uid VARCHAR(200),
    sop_code VARCHAR(20),
    sop_description TEXT,
    procedure_code VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Claims table (insurance claims)
CREATE TABLE clinical_data.claims (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    provider_id UUID REFERENCES clinical_data.providers(id),
    primary_patient_insurance_id UUID,
    secondary_patient_insurance_id UUID,
    department_id INTEGER,
    patient_department_id INTEGER,
    diagnosis1 VARCHAR(20),
    diagnosis2 VARCHAR(20),
    diagnosis3 VARCHAR(20),
    diagnosis4 VARCHAR(20),
    diagnosis5 VARCHAR(20),
    diagnosis6 VARCHAR(20),
    diagnosis7 VARCHAR(20),
    diagnosis8 VARCHAR(20),
    referring_provider_id UUID,
    appointment_id UUID,
    current_illness_date DATE,
    service_date DATE,
    supervisor_id UUID,
    status1 VARCHAR(20),
    status2 VARCHAR(20),
    statusp VARCHAR(20),
    outstanding1 DECIMAL(10, 2),
    outstanding2 DECIMAL(10, 2),
    outstandingp DECIMAL(10, 2),
    last_billed_date1 DATE,
    last_billed_date2 DATE,
    last_billed_datep DATE,
    healthcare_claim_type_id1 INTEGER,
    healthcare_claim_type_id2 INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Claims Transactions table
CREATE TABLE clinical_data.claims_transactions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    claim_id UUID NOT NULL REFERENCES clinical_data.claims(id),
    charge_id INTEGER,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    type INTEGER,
    amount DECIMAL(10, 2),
    method INTEGER,
    from_date DATE,
    to_date DATE,
    place_of_service INTEGER,
    procedure_code VARCHAR(20),
    modifier1 VARCHAR(10),
    modifier2 VARCHAR(10),
    diagnosis_ref1 INTEGER,
    diagnosis_ref2 INTEGER,
    diagnosis_ref3 INTEGER,
    diagnosis_ref4 INTEGER,
    units INTEGER,
    department_id INTEGER,
    notes TEXT,
    unit_amount DECIMAL(10, 2),
    transfer_out_id INTEGER,
    transfer_type INTEGER,
    payments DECIMAL(10, 2),
    adjustments DECIMAL(10, 2),
    transfers DECIMAL(10, 2),
    outstanding DECIMAL(10, 2),
    appointment_id UUID,
    line_note TEXT,
    patient_insurance_id UUID,
    fee_schedule_id INTEGER,
    provider_id UUID REFERENCES clinical_data.providers(id),
    supervisor_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payer Transitions table (insurance changes)
CREATE TABLE clinical_data.payer_transitions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    patient_id UUID NOT NULL REFERENCES clinical_data.patients(id),
    member_id VARCHAR(50),
    start_date DATE NOT NULL,
    end_date DATE,
    payer_id UUID NOT NULL REFERENCES clinical_data.payers(id),
    secondary_payer_id UUID REFERENCES clinical_data.payers(id),
    plan_ownership VARCHAR(50),
    owner_name VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Patient indexes
CREATE INDEX idx_patients_birth_date ON clinical_data.patients(birth_date);
CREATE INDEX idx_patients_gender ON clinical_data.patients(gender);
CREATE INDEX idx_patients_race ON clinical_data.patients(race);
CREATE INDEX idx_patients_ethnicity ON clinical_data.patients(ethnicity);
CREATE INDEX idx_patients_city ON clinical_data.patients(city);
CREATE INDEX idx_patients_state ON clinical_data.patients(state);
CREATE INDEX idx_patients_zip ON clinical_data.patients(zip);

-- Encounter indexes
CREATE INDEX idx_encounters_patient_id ON clinical_data.encounters(patient_id);
CREATE INDEX idx_encounters_start_time ON clinical_data.encounters(start_time);
CREATE INDEX idx_encounters_provider_id ON clinical_data.encounters(provider_id);
CREATE INDEX idx_encounters_organization_id ON clinical_data.encounters(organization_id);
CREATE INDEX idx_encounters_encounter_class ON clinical_data.encounters(encounter_class);

-- Condition indexes
CREATE INDEX idx_conditions_patient_id ON clinical_data.conditions(patient_id);
CREATE INDEX idx_conditions_start_date ON clinical_data.conditions(start_date);
CREATE INDEX idx_conditions_code ON clinical_data.conditions(code);
CREATE INDEX idx_conditions_system ON clinical_data.conditions(system);
CREATE INDEX idx_conditions_encounter_id ON clinical_data.conditions(encounter_id);

-- Medication indexes
CREATE INDEX idx_medications_patient_id ON clinical_data.medications(patient_id);
CREATE INDEX idx_medications_start_date ON clinical_data.medications(start_date);
CREATE INDEX idx_medications_code ON clinical_data.medications(code);
CREATE INDEX idx_medications_encounter_id ON clinical_data.medications(encounter_id);

-- Procedure indexes
CREATE INDEX idx_procedures_patient_id ON clinical_data.procedures(patient_id);
CREATE INDEX idx_procedures_date ON clinical_data.procedures(date);
CREATE INDEX idx_procedures_code ON clinical_data.procedures(code);
CREATE INDEX idx_procedures_encounter_id ON clinical_data.procedures(encounter_id);

-- Observation indexes
CREATE INDEX idx_observations_patient_id ON clinical_data.observations(patient_id);
CREATE INDEX idx_observations_date ON clinical_data.observations(date);
CREATE INDEX idx_observations_code ON clinical_data.observations(code);
CREATE INDEX idx_observations_category ON clinical_data.observations(category);
CREATE INDEX idx_observations_encounter_id ON clinical_data.observations(encounter_id);

-- Provider indexes
CREATE INDEX idx_providers_organization_id ON clinical_data.providers(organization_id);
CREATE INDEX idx_providers_speciality ON clinical_data.providers(speciality);
CREATE INDEX idx_providers_city ON clinical_data.providers(city);
CREATE INDEX idx_providers_state ON clinical_data.providers(state);

-- Organization indexes
CREATE INDEX idx_organizations_city ON clinical_data.organizations(city);
CREATE INDEX idx_organizations_state ON clinical_data.organizations(state);
CREATE INDEX idx_organizations_name ON clinical_data.organizations(name);

-- =====================================================
-- VIEWS FOR COMMON QUERIES
-- =====================================================

-- Patient summary view
CREATE VIEW clinical_data.patient_summary AS
SELECT 
    p.id,
    p.first_name,
    p.last_name,
    p.gender,
    p.birth_date,
    EXTRACT(YEAR FROM AGE(COALESCE(p.death_date, CURRENT_DATE), p.birth_date)) AS age,
    p.race,
    p.ethnicity,
    p.city,
    p.state,
    COUNT(DISTINCT e.id) AS total_encounters,
    COUNT(DISTINCT c.id) AS total_conditions,
    COUNT(DISTINCT m.id) AS total_medications,
    p.healthcare_expenses,
    p.healthcare_coverage
FROM clinical_data.patients p
LEFT JOIN clinical_data.encounters e ON p.id = e.patient_id
LEFT JOIN clinical_data.conditions c ON p.id = c.patient_id
LEFT JOIN clinical_data.medications m ON p.id = m.patient_id
GROUP BY p.id, p.first_name, p.last_name, p.gender, p.birth_date, p.race, p.ethnicity, 
         p.city, p.state, p.healthcare_expenses, p.healthcare_coverage, p.death_date;

-- Recent encounters view
CREATE VIEW clinical_data.recent_encounters AS
SELECT 
    e.id,
    e.start_time,
    e.stop_time,
    p.first_name || ' ' || p.last_name AS patient_name,
    p.id AS patient_id,
    e.description AS encounter_description,
    e.encounter_class,
    o.name AS organization_name,
    pr.name AS provider_name,
    e.total_claim_cost
FROM clinical_data.encounters e
JOIN clinical_data.patients p ON e.patient_id = p.id
LEFT JOIN clinical_data.organizations o ON e.organization_id = o.id
LEFT JOIN clinical_data.providers pr ON e.provider_id = pr.id
WHERE e.start_time >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY e.start_time DESC;

-- Active conditions view
CREATE VIEW clinical_data.active_conditions AS
SELECT 
    c.id,
    c.start_date,
    c.stop_date,
    p.first_name || ' ' || p.last_name AS patient_name,
    p.id AS patient_id,
    c.code,
    c.description,
    c.system
FROM clinical_data.conditions c
JOIN clinical_data.patients p ON c.patient_id = p.id
WHERE c.stop_date IS NULL OR c.stop_date > CURRENT_DATE
ORDER BY c.start_date DESC;

-- Current medications view
CREATE VIEW clinical_data.current_medications AS
SELECT 
    m.id,
    m.start_date,
    m.stop_date,
    p.first_name || ' ' || p.last_name AS patient_name,
    p.id AS patient_id,
    m.code,
    m.description,
    m.total_cost,
    m.reason_description
FROM clinical_data.medications m
JOIN clinical_data.patients p ON m.patient_id = p.id
WHERE m.stop_date IS NULL OR m.stop_date > CURRENT_DATE
ORDER BY m.start_date DESC;

-- =====================================================
-- FUNCTIONS FOR DATA QUALITY
-- =====================================================

-- Function to calculate patient age
CREATE OR REPLACE FUNCTION clinical_data.calculate_age(birth_date DATE, reference_date DATE DEFAULT CURRENT_DATE)
RETURNS INTEGER AS $$
BEGIN
    RETURN EXTRACT(YEAR FROM AGE(reference_date, birth_date));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to get patient's active conditions
CREATE OR REPLACE FUNCTION clinical_data.get_active_conditions(patient_uuid UUID)
RETURNS TABLE(condition_code VARCHAR, condition_description TEXT, start_date DATE) AS $$
BEGIN
    RETURN QUERY
    SELECT c.code, c.description, c.start_date
    FROM clinical_data.conditions c
    WHERE c.patient_id = patient_uuid
    AND (c.stop_date IS NULL OR c.stop_date > CURRENT_DATE)
    ORDER BY c.start_date DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get patient's recent encounters
CREATE OR REPLACE FUNCTION clinical_data.get_recent_encounters(patient_uuid UUID, days_back INTEGER DEFAULT 30)
RETURNS TABLE(encounter_id UUID, encounter_date TIMESTAMP, description TEXT, provider_name VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT e.id, e.start_time, e.description, pr.name
    FROM clinical_data.encounters e
    LEFT JOIN clinical_data.providers pr ON e.provider_id = pr.id
    WHERE e.patient_id = patient_uuid
    AND e.start_time >= CURRENT_DATE - INTERVAL '1 day' * days_back
    ORDER BY e.start_time DESC;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- GRANTS AND PERMISSIONS
-- =====================================================

-- Create roles for different access levels
CREATE ROLE clinical_readonly;
CREATE ROLE clinical_analyst;
CREATE ROLE clinical_admin;

-- Grant permissions to readonly role
GRANT USAGE ON SCHEMA clinical_data TO clinical_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA clinical_data TO clinical_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA clinical_data TO clinical_readonly;

-- Grant permissions to analyst role (includes readonly + some modifications)
GRANT clinical_readonly TO clinical_analyst;
GRANT INSERT, UPDATE ON clinical_data.observations TO clinical_analyst;
GRANT INSERT, UPDATE ON clinical_data.procedures TO clinical_analyst;

-- Grant permissions to admin role (full access)
GRANT ALL PRIVILEGES ON SCHEMA clinical_data TO clinical_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA clinical_data TO clinical_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA clinical_data TO clinical_admin;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA clinical_data GRANT SELECT ON TABLES TO clinical_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA clinical_data GRANT ALL ON TABLES TO clinical_admin;

COMMENT ON SCHEMA clinical_data IS 'Clinical data schema for NLQ AI Assistant - contains synthetic patient data from Synthea';