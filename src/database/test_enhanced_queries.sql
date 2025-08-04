-- Test Queries for Enhanced Clinical Data
-- This file contains SQL queries to answer all the clinical questions

-- 1. How many patients received an HPV vaccine?
SELECT COUNT(DISTINCT patient) as hpv_vaccine_patients
FROM clinical_data.immunizations 
WHERE description ILIKE '%papillomavirus%' OR description ILIKE '%hpv%';

-- 2. How many patients were diagnosed with sinusitis?
SELECT COUNT(DISTINCT patient) as sinusitis_patients
FROM clinical_data.conditions 
WHERE description ILIKE '%sinusitis%';

-- 3. How many patients received vaccine - HPV? (Alternative phrasing)
SELECT COUNT(DISTINCT patient) as hpv_vaccine_recipients
FROM clinical_data.immunizations 
WHERE code = 90649 OR description ILIKE '%papillomavirus%';

-- 4. List all medications prescribed in 2019
SELECT DISTINCT description as medication_name, COUNT(*) as prescription_count
FROM clinical_data.medications 
WHERE EXTRACT(YEAR FROM start_date) = 2019
GROUP BY description
ORDER BY prescription_count DESC;

-- 5. How many procedures were done in 2020?
SELECT COUNT(*) as procedures_2020
FROM clinical_data.procedures 
WHERE EXTRACT(YEAR FROM start::date) = 2020;

-- 6. Show all medications prescribed in 2021
SELECT DISTINCT description as medication_name, COUNT(*) as prescription_count
FROM clinical_data.medications 
WHERE EXTRACT(YEAR FROM start_date) = 2021
GROUP BY description
ORDER BY prescription_count DESC;

-- 7. Top 5 most common conditions
SELECT description as condition_name, COUNT(*) as occurrence_count
FROM clinical_data.conditions
GROUP BY description
ORDER BY occurrence_count DESC
LIMIT 5;

-- 8. Most frequent vaccines given
SELECT description as vaccine_name, COUNT(*) as administration_count
FROM clinical_data.immunizations
GROUP BY description
ORDER BY administration_count DESC;

-- 9. What are the top 5 most common medications prescribed?
SELECT description as medication_name, COUNT(*) as prescription_count
FROM clinical_data.medications
GROUP BY description
ORDER BY prescription_count DESC
LIMIT 5;

-- 10. Top 5 most frequent diagnoses in conditions
SELECT description as diagnosis, COUNT(*) as frequency
FROM clinical_data.conditions
GROUP BY description
ORDER BY frequency DESC
LIMIT 5;

-- 11. List all distinct vaccines given to patients
SELECT DISTINCT description as vaccine_name
FROM clinical_data.immunizations
ORDER BY vaccine_name;

-- 12. List all procedures involving anxiety
SELECT p.description as procedure_name, COUNT(*) as procedure_count
FROM clinical_data.procedures p
WHERE p.reasondescription ILIKE '%anxiety%'
GROUP BY p.description
ORDER BY procedure_count DESC;

-- 13. List all procedures not involving anxiety
SELECT p.description as procedure_name, COUNT(*) as procedure_count
FROM clinical_data.procedures p
WHERE p.reasondescription IS NULL OR p.reasondescription NOT ILIKE '%anxiety%'
GROUP BY p.description
ORDER BY procedure_count DESC;

-- 14. Which payers covered more than 100 patients?
SELECT p.name as payer_name, p.unique_customers as patient_count
FROM clinical_data.payers p
WHERE p.unique_customers > 100
ORDER BY p.unique_customers DESC;

-- Alternative query using payer_transitions table
SELECT p.name as payer_name, COUNT(DISTINCT pt.patient_id) as patient_count
FROM clinical_data.payers p
JOIN clinical_data.payer_transitions pt ON p.id = pt.payer_id
GROUP BY p.id, p.name
HAVING COUNT(DISTINCT pt.patient_id) > 100
ORDER BY patient_count DESC;

-- 15. How many patients received more than 2 immunizations?
SELECT COUNT(*) as patients_with_multiple_immunizations
FROM (
    SELECT patient, COUNT(*) as immunization_count
    FROM clinical_data.immunizations
    GROUP BY patient
    HAVING COUNT(*) > 2
) subquery;

-- Additional useful queries for comprehensive testing:

-- Count of each vaccine type
SELECT description as vaccine_type, COUNT(*) as count
FROM clinical_data.immunizations
GROUP BY description
ORDER BY count DESC;

-- Procedures by year
SELECT EXTRACT(YEAR FROM start::date) as year, COUNT(*) as procedure_count
FROM clinical_data.procedures
GROUP BY EXTRACT(YEAR FROM start::date)
ORDER BY year;

-- Medications by year
SELECT EXTRACT(YEAR FROM start_date) as year, COUNT(*) as medication_count
FROM clinical_data.medications
GROUP BY EXTRACT(YEAR FROM start_date)
ORDER BY year;

-- Conditions by year
SELECT EXTRACT(YEAR FROM start::date) as year, COUNT(*) as condition_count
FROM clinical_data.conditions
GROUP BY EXTRACT(YEAR FROM start::date)
ORDER BY year;

-- Patient demographics summary
SELECT 
    gender,
    COUNT(*) as patient_count,
    AVG(EXTRACT(YEAR FROM AGE(COALESCE(death_date, CURRENT_DATE), birth_date))) as avg_age
FROM clinical_data.patients
GROUP BY gender;

-- Most common encounter types
SELECT encounter_class, COUNT(*) as encounter_count
FROM clinical_data.encounters
GROUP BY encounter_class
ORDER BY encounter_count DESC;

-- Provider specialties
SELECT speciality, COUNT(*) as provider_count
FROM clinical_data.providers
WHERE speciality IS NOT NULL
GROUP BY speciality
ORDER BY provider_count DESC;

-- Organization utilization
SELECT name, utilization
FROM clinical_data.organizations
WHERE utilization IS NOT NULL
ORDER BY utilization DESC
LIMIT 10;