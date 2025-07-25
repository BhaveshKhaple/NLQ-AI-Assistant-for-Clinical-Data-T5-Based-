# Clinical Database Entity-Relationship Diagram (ERD)
*Generated on: 2025-07-25 22:03:54*

## Database Overview
- **Database**: medical
- **Schema**: clinical_data
- **Total Tables**: 19
- **Total Views**: 4
- **Total Relationships**: 14

## Table Summary

| Table | Rows | Columns | Primary Key | Foreign Keys |
|-------|------|---------|-------------|--------------|
| providers | 272 | 13 | id | 1 |
| organizations | 272 | 12 | id | 0 |
| encounters | 7,217 | 16 | id | 4 |
| payers | 10 | 23 | id | 0 |
| care_plans | 0 | 11 | id | 2 |
| conditions | 0 | 9 | id | 2 |
| medications | 5,750 | 15 | id | 3 |
| patients | 107 | 30 | id | 0 |
| claims | 0 | 32 | id | 2 |
| procedures | 17,621 | 10 |  | 0 |
| observations | 84,503 | 9 |  | 0 |
| immunizations | 1,569 | 6 |  | 0 |
| allergies | 119 | 15 |  | 0 |
| careplans | 0 | 9 |  | 0 |
| devices | 0 | 7 |  | 0 |
| supplies | 0 | 6 |  | 0 |
| imaging_studies | 0 | 13 |  | 0 |
| payer_transitions | 0 | 8 |  | 0 |
| claims_transactions | 0 | 33 |  | 0 |

## Entity-Relationship Diagram

```mermaid
erDiagram

    PROVIDERS {
        UUID id PK,NOT NULL
        UUID organization_id FK
        VARCHAR name NOT NULL
        VARCHAR gender
        VARCHAR speciality
        VARCHAR address
        VARCHAR city
        VARCHAR state
        VARCHAR zip
        NUMERIC latitude
        NUMERIC longitude
        INTEGER utilization
        TIMESTAMP created_at
    }

    ORGANIZATIONS {
        UUID id PK,NOT NULL
        VARCHAR name NOT NULL
        VARCHAR address
        VARCHAR city
        VARCHAR state
        VARCHAR zip
        NUMERIC latitude
        NUMERIC longitude
        VARCHAR phone
        NUMERIC revenue
        INTEGER utilization
        TIMESTAMP created_at
    }

    ENCOUNTERS {
        UUID id PK,NOT NULL
        TIMESTAMP start_time NOT NULL
        TIMESTAMP stop_time
        UUID patient_id FK,NOT NULL
        UUID organization_id FK
        UUID provider_id FK
        UUID payer_id FK
        VARCHAR encounter_class
        VARCHAR code
        TEXT description
        NUMERIC base_encounter_cost
        NUMERIC total_claim_cost
        NUMERIC payer_coverage
        VARCHAR reason_code
        TEXT reason_description
        TIMESTAMP created_at
    }

    PAYERS {
        UUID id PK,NOT NULL
        VARCHAR name NOT NULL
        VARCHAR ownership
        VARCHAR address
        VARCHAR city
        VARCHAR state
        VARCHAR zip
        VARCHAR phone
        NUMERIC amount_covered
        NUMERIC amount_uncovered
        NUMERIC revenue
        INTEGER covered_encounters
        INTEGER uncovered_encounters
        INTEGER covered_medications
        INTEGER uncovered_medications
        INTEGER covered_procedures
        INTEGER uncovered_procedures
        INTEGER covered_immunizations
        INTEGER uncovered_immunizations
        INTEGER unique_customers
        NUMERIC qols_avg
        INTEGER member_months
        TIMESTAMP created_at
    }

    MEDICATIONS {
        UUID id PK,NOT NULL
        DATE start_date NOT NULL
        DATE stop_date
        UUID patient_id FK,NOT NULL
        UUID payer_id FK
        UUID encounter_id FK
        VARCHAR code
        TEXT description NOT NULL
        NUMERIC base_cost
        NUMERIC payer_coverage
        INTEGER dispenses
        NUMERIC total_cost
        VARCHAR reason_code
        TEXT reason_description
        TIMESTAMP created_at
    }

    PATIENTS {
        UUID id PK,NOT NULL
        DATE birth_date NOT NULL
        DATE death_date
        VARCHAR ssn
        VARCHAR drivers
        VARCHAR passport
        VARCHAR prefix
        VARCHAR first_name
        VARCHAR middle_name
        VARCHAR last_name
        VARCHAR suffix
        VARCHAR maiden_name
        VARCHAR marital_status
        VARCHAR race
        VARCHAR ethnicity
        VARCHAR gender NOT NULL
        VARCHAR birth_place
        VARCHAR address
        VARCHAR city
        VARCHAR state
        VARCHAR county
        VARCHAR fips
        VARCHAR zip
        NUMERIC latitude
        NUMERIC longitude
        NUMERIC healthcare_expenses
        NUMERIC healthcare_coverage
        NUMERIC income
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    PROCEDURES {
        TEXT start
        TEXT stop
        TEXT patient
        TEXT encounter
        TEXT system
        BIGINT code
        TEXT description
        DOUBLE PRECISION base_cost
        DOUBLE PRECISION reasoncode
        TEXT reasondescription
    }

    OBSERVATIONS {
        TIMESTAMP date
        TEXT patient
        TEXT encounter
        TEXT category
        TEXT code
        TEXT description
        TEXT value
        TEXT units
        TEXT type
    }

    IMMUNIZATIONS {
        TEXT date
        TEXT patient
        TEXT encounter
        BIGINT code
        TEXT description
        DOUBLE PRECISION base_cost
    }

    ALLERGIES {
        TEXT start
        DOUBLE PRECISION stop
        TEXT patient
        TEXT encounter
        BIGINT code
        TEXT system
        TEXT description
        TEXT type
        TEXT category
        DOUBLE PRECISION reaction1
        TEXT description1
        TEXT severity1
        DOUBLE PRECISION reaction2
        TEXT description2
        TEXT severity2
    }

    PROVIDERS ||--o{ ORGANIZATIONS : organization_id
    ENCOUNTERS ||--o{ ORGANIZATIONS : organization_id
    ENCOUNTERS ||--o{ PATIENTS : patient_id
    ENCOUNTERS ||--o{ PAYERS : payer_id
    ENCOUNTERS ||--o{ PROVIDERS : provider_id
    MEDICATIONS ||--o{ ENCOUNTERS : encounter_id
    MEDICATIONS ||--o{ PATIENTS : patient_id
    MEDICATIONS ||--o{ PAYERS : payer_id
```

## Detailed Table Specifications

### Providers
**Rows**: 272
**Primary Key**: id

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | False |  | PRIMARY KEY, NOT NULL |
| organization_id | UUID | True |  | FK → organizations.id |
| name | VARCHAR(200) | False |  | NOT NULL |
| gender | VARCHAR(1) | True |  |  |
| speciality | VARCHAR(100) | True |  |  |
| address | VARCHAR(200) | True |  |  |
| city | VARCHAR(100) | True |  |  |
| state | VARCHAR(50) | True |  |  |
| zip | VARCHAR(15) | True |  |  |
| latitude | NUMERIC(10, 8) | True |  |  |
| longitude | NUMERIC(11, 8) | True |  |  |
| utilization | INTEGER | True |  |  |
| created_at | TIMESTAMP | True | CURRENT_TIMESTAMP |  |

#### Foreign Key Relationships
- `organization_id` → `organizations.id`

#### Indexes
- `idx_providers_city` on (city)
- `idx_providers_organization_id` on (organization_id)
- `idx_providers_speciality` on (speciality)
- `idx_providers_state` on (state)


### Organizations
**Rows**: 272
**Primary Key**: id

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | False |  | PRIMARY KEY, NOT NULL |
| name | VARCHAR(200) | False |  | NOT NULL |
| address | VARCHAR(200) | True |  |  |
| city | VARCHAR(100) | True |  |  |
| state | VARCHAR(50) | True |  |  |
| zip | VARCHAR(15) | True |  |  |
| latitude | NUMERIC(10, 8) | True |  |  |
| longitude | NUMERIC(11, 8) | True |  |  |
| phone | VARCHAR(50) | True |  |  |
| revenue | NUMERIC(15, 2) | True |  |  |
| utilization | INTEGER | True |  |  |
| created_at | TIMESTAMP | True | CURRENT_TIMESTAMP |  |

#### Indexes
- `idx_organizations_city` on (city)
- `idx_organizations_name` on (name)
- `idx_organizations_state` on (state)


### Encounters
**Rows**: 7,217
**Primary Key**: id

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | False |  | PRIMARY KEY, NOT NULL |
| start_time | TIMESTAMP | False |  | NOT NULL |
| stop_time | TIMESTAMP | True |  |  |
| patient_id | UUID | False |  | FK → patients.id, NOT NULL |
| organization_id | UUID | True |  | FK → organizations.id |
| provider_id | UUID | True |  | FK → providers.id |
| payer_id | UUID | True |  | FK → payers.id |
| encounter_class | VARCHAR(50) | True |  |  |
| code | VARCHAR(50) | True |  |  |
| description | TEXT | True |  |  |
| base_encounter_cost | NUMERIC(10, 2) | True |  |  |
| total_claim_cost | NUMERIC(10, 2) | True |  |  |
| payer_coverage | NUMERIC(10, 2) | True |  |  |
| reason_code | VARCHAR(50) | True |  |  |
| reason_description | TEXT | True |  |  |
| created_at | TIMESTAMP | True | CURRENT_TIMESTAMP |  |

#### Foreign Key Relationships
- `organization_id` → `organizations.id`
- `patient_id` → `patients.id`
- `payer_id` → `payers.id`
- `provider_id` → `providers.id`

#### Indexes
- `idx_encounters_date_range` on (start_time, stop_time)
- `idx_encounters_encounter_class` on (encounter_class)
- `idx_encounters_organization_id` on (organization_id)
- `idx_encounters_patient_id` on (patient_id)
- `idx_encounters_provider_id` on (provider_id)
- `idx_encounters_start_time` on (start_time)


### Payers
**Rows**: 10
**Primary Key**: id

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | False |  | PRIMARY KEY, NOT NULL |
| name | VARCHAR(200) | False |  | NOT NULL |
| ownership | VARCHAR(50) | True |  |  |
| address | VARCHAR(200) | True |  |  |
| city | VARCHAR(100) | True |  |  |
| state | VARCHAR(50) | True |  |  |
| zip | VARCHAR(15) | True |  |  |
| phone | VARCHAR(50) | True |  |  |
| amount_covered | NUMERIC(15, 2) | True |  |  |
| amount_uncovered | NUMERIC(15, 2) | True |  |  |
| revenue | NUMERIC(15, 2) | True |  |  |
| covered_encounters | INTEGER | True |  |  |
| uncovered_encounters | INTEGER | True |  |  |
| covered_medications | INTEGER | True |  |  |
| uncovered_medications | INTEGER | True |  |  |
| covered_procedures | INTEGER | True |  |  |
| uncovered_procedures | INTEGER | True |  |  |
| covered_immunizations | INTEGER | True |  |  |
| uncovered_immunizations | INTEGER | True |  |  |
| unique_customers | INTEGER | True |  |  |
| qols_avg | NUMERIC(5, 3) | True |  |  |
| member_months | INTEGER | True |  |  |
| created_at | TIMESTAMP | True | CURRENT_TIMESTAMP |  |


### Care_Plans
**Rows**: 0
**Primary Key**: id

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | False | clinical_data.uuid_generate_v4() | PRIMARY KEY, NOT NULL |
| start_date | DATE | False |  | NOT NULL |
| stop_date | DATE | True |  |  |
| patient_id | UUID | False |  | FK → patients.id, NOT NULL |
| encounter_id | UUID | True |  | FK → encounters.id |
| system | VARCHAR(50) | True |  |  |
| code | VARCHAR(50) | False |  | NOT NULL |
| description | TEXT | False |  | NOT NULL |
| reason_code | VARCHAR(50) | True |  |  |
| reason_description | TEXT | True |  |  |
| created_at | TIMESTAMP | True | CURRENT_TIMESTAMP |  |

#### Foreign Key Relationships
- `encounter_id` → `encounters.id`
- `patient_id` → `patients.id`


### Conditions
**Rows**: 0
**Primary Key**: id

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | False | clinical_data.uuid_generate_v4() | PRIMARY KEY, NOT NULL |
| start_date | DATE | False |  | NOT NULL |
| stop_date | DATE | True |  |  |
| patient_id | UUID | False |  | FK → patients.id, NOT NULL |
| encounter_id | UUID | True |  | FK → encounters.id |
| system | VARCHAR(50) | False |  | NOT NULL |
| code | VARCHAR(20) | False |  | NOT NULL |
| description | TEXT | False |  | NOT NULL |
| created_at | TIMESTAMP | True | CURRENT_TIMESTAMP |  |

#### Foreign Key Relationships
- `encounter_id` → `encounters.id`
- `patient_id` → `patients.id`

#### Indexes
- `idx_conditions_code` on (code)
- `idx_conditions_date_range` on (start_date, stop_date)
- `idx_conditions_encounter_id` on (encounter_id)
- `idx_conditions_patient_id` on (patient_id)
- `idx_conditions_start_date` on (start_date)
- `idx_conditions_system` on (system)


### Medications
**Rows**: 5,750
**Primary Key**: id

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | False | clinical_data.uuid_generate_v4() | PRIMARY KEY, NOT NULL |
| start_date | DATE | False |  | NOT NULL |
| stop_date | DATE | True |  |  |
| patient_id | UUID | False |  | FK → patients.id, NOT NULL |
| payer_id | UUID | True |  | FK → payers.id |
| encounter_id | UUID | True |  | FK → encounters.id |
| code | VARCHAR(20) | True |  |  |
| description | TEXT | False |  | NOT NULL |
| base_cost | NUMERIC(10, 2) | True |  |  |
| payer_coverage | NUMERIC(10, 2) | True |  |  |
| dispenses | INTEGER | True |  |  |
| total_cost | NUMERIC(10, 2) | True |  |  |
| reason_code | VARCHAR(50) | True |  |  |
| reason_description | TEXT | True |  |  |
| created_at | TIMESTAMP | True | CURRENT_TIMESTAMP |  |

#### Foreign Key Relationships
- `encounter_id` → `encounters.id`
- `patient_id` → `patients.id`
- `payer_id` → `payers.id`

#### Indexes
- `idx_medications_code` on (code)
- `idx_medications_date_range` on (start_date, stop_date)
- `idx_medications_encounter_id` on (encounter_id)
- `idx_medications_patient_id` on (patient_id)
- `idx_medications_start_date` on (start_date)


### Patients
**Rows**: 107
**Primary Key**: id

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | False |  | PRIMARY KEY, NOT NULL |
| birth_date | DATE | False |  | NOT NULL |
| death_date | DATE | True |  |  |
| ssn | VARCHAR(15) | True |  |  |
| drivers | VARCHAR(15) | True |  |  |
| passport | VARCHAR(15) | True |  |  |
| prefix | VARCHAR(10) | True |  |  |
| first_name | VARCHAR(50) | True |  |  |
| middle_name | VARCHAR(50) | True |  |  |
| last_name | VARCHAR(50) | True |  |  |
| suffix | VARCHAR(10) | True |  |  |
| maiden_name | VARCHAR(50) | True |  |  |
| marital_status | VARCHAR(1) | True |  |  |
| race | VARCHAR(50) | True |  |  |
| ethnicity | VARCHAR(50) | True |  |  |
| gender | VARCHAR(1) | False |  | NOT NULL |
| birth_place | VARCHAR(200) | True |  |  |
| address | VARCHAR(200) | True |  |  |
| city | VARCHAR(100) | True |  |  |
| state | VARCHAR(50) | True |  |  |
| county | VARCHAR(100) | True |  |  |
| fips | VARCHAR(10) | True |  |  |
| zip | VARCHAR(15) | True |  |  |
| latitude | NUMERIC(10, 8) | True |  |  |
| longitude | NUMERIC(11, 8) | True |  |  |
| healthcare_expenses | NUMERIC(12, 2) | True |  |  |
| healthcare_coverage | NUMERIC(12, 2) | True |  |  |
| income | NUMERIC(12, 2) | True |  |  |
| created_at | TIMESTAMP | True | CURRENT_TIMESTAMP |  |
| updated_at | TIMESTAMP | True | CURRENT_TIMESTAMP |  |

#### Indexes
- `idx_patients_birth_date` on (birth_date)
- `idx_patients_city` on (city)
- `idx_patients_ethnicity` on (ethnicity)
- `idx_patients_gender` on (gender)
- `idx_patients_race` on (race)
- `idx_patients_state` on (state)
- `idx_patients_zip` on (zip)


### Claims
**Rows**: 0
**Primary Key**: id

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | UUID | False | clinical_data.uuid_generate_v4() | PRIMARY KEY, NOT NULL |
| patient_id | UUID | False |  | FK → patients.id, NOT NULL |
| provider_id | UUID | True |  | FK → providers.id |
| primary_patient_insurance_id | UUID | True |  |  |
| secondary_patient_insurance_id | UUID | True |  |  |
| department_id | INTEGER | True |  |  |
| patient_department_id | INTEGER | True |  |  |
| diagnosis1 | VARCHAR(50) | True |  |  |
| diagnosis2 | VARCHAR(50) | True |  |  |
| diagnosis3 | VARCHAR(50) | True |  |  |
| diagnosis4 | VARCHAR(50) | True |  |  |
| diagnosis5 | VARCHAR(50) | True |  |  |
| diagnosis6 | VARCHAR(50) | True |  |  |
| diagnosis7 | VARCHAR(50) | True |  |  |
| diagnosis8 | VARCHAR(50) | True |  |  |
| referring_provider_id | UUID | True |  |  |
| appointment_id | UUID | True |  |  |
| current_illness_date | DATE | True |  |  |
| service_date | DATE | True |  |  |
| supervisor_id | UUID | True |  |  |
| status1 | VARCHAR(50) | True |  |  |
| status2 | VARCHAR(50) | True |  |  |
| statusp | VARCHAR(50) | True |  |  |
| outstanding1 | NUMERIC(10, 2) | True |  |  |
| outstanding2 | NUMERIC(10, 2) | True |  |  |
| outstandingp | NUMERIC(10, 2) | True |  |  |
| last_billed_date1 | DATE | True |  |  |
| last_billed_date2 | DATE | True |  |  |
| last_billed_datep | DATE | True |  |  |
| healthcare_claim_type_id1 | INTEGER | True |  |  |
| healthcare_claim_type_id2 | INTEGER | True |  |  |
| created_at | TIMESTAMP | True | CURRENT_TIMESTAMP |  |

#### Foreign Key Relationships
- `patient_id` → `patients.id`
- `provider_id` → `providers.id`


### Procedures
**Rows**: 17,621
**Primary Key**: None

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| start | TEXT | True |  |  |
| stop | TEXT | True |  |  |
| patient | TEXT | True |  |  |
| encounter | TEXT | True |  |  |
| system | TEXT | True |  |  |
| code | BIGINT | True |  |  |
| description | TEXT | True |  |  |
| base_cost | DOUBLE PRECISION | True |  |  |
| reasoncode | DOUBLE PRECISION | True |  |  |
| reasondescription | TEXT | True |  |  |


### Observations
**Rows**: 84,503
**Primary Key**: None

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| date | TIMESTAMP | True |  |  |
| patient | TEXT | True |  |  |
| encounter | TEXT | True |  |  |
| category | TEXT | True |  |  |
| code | TEXT | True |  |  |
| description | TEXT | True |  |  |
| value | TEXT | True |  |  |
| units | TEXT | True |  |  |
| type | TEXT | True |  |  |


### Immunizations
**Rows**: 1,569
**Primary Key**: None

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| date | TEXT | True |  |  |
| patient | TEXT | True |  |  |
| encounter | TEXT | True |  |  |
| code | BIGINT | True |  |  |
| description | TEXT | True |  |  |
| base_cost | DOUBLE PRECISION | True |  |  |


### Allergies
**Rows**: 119
**Primary Key**: None

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| start | TEXT | True |  |  |
| stop | DOUBLE PRECISION | True |  |  |
| patient | TEXT | True |  |  |
| encounter | TEXT | True |  |  |
| code | BIGINT | True |  |  |
| system | TEXT | True |  |  |
| description | TEXT | True |  |  |
| type | TEXT | True |  |  |
| category | TEXT | True |  |  |
| reaction1 | DOUBLE PRECISION | True |  |  |
| description1 | TEXT | True |  |  |
| severity1 | TEXT | True |  |  |
| reaction2 | DOUBLE PRECISION | True |  |  |
| description2 | TEXT | True |  |  |
| severity2 | TEXT | True |  |  |


### Careplans
**Rows**: 0
**Primary Key**: None

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | TEXT | True |  |  |
| start | TEXT | True |  |  |
| stop | TEXT | True |  |  |
| patient | TEXT | True |  |  |
| encounter | TEXT | True |  |  |
| code | BIGINT | True |  |  |
| description | TEXT | True |  |  |
| reasoncode | DOUBLE PRECISION | True |  |  |
| reasondescription | TEXT | True |  |  |


### Devices
**Rows**: 0
**Primary Key**: None

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| start | TEXT | True |  |  |
| stop | TEXT | True |  |  |
| patient | TEXT | True |  |  |
| encounter | TEXT | True |  |  |
| code | BIGINT | True |  |  |
| description | TEXT | True |  |  |
| udi | TEXT | True |  |  |


### Supplies
**Rows**: 0
**Primary Key**: None

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| date | TEXT | True |  |  |
| patient | TEXT | True |  |  |
| encounter | TEXT | True |  |  |
| code | BIGINT | True |  |  |
| description | TEXT | True |  |  |
| quantity | BIGINT | True |  |  |


### Imaging_Studies
**Rows**: 0
**Primary Key**: None

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | TEXT | True |  |  |
| date | TEXT | True |  |  |
| patient | TEXT | True |  |  |
| encounter | TEXT | True |  |  |
| series_uid | TEXT | True |  |  |
| bodysite_code | BIGINT | True |  |  |
| bodysite_description | TEXT | True |  |  |
| modality_code | TEXT | True |  |  |
| modality_description | TEXT | True |  |  |
| instance_uid | TEXT | True |  |  |
| sop_code | TEXT | True |  |  |
| sop_description | TEXT | True |  |  |
| procedure_code | BIGINT | True |  |  |


### Payer_Transitions
**Rows**: 0
**Primary Key**: None

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| patient | TEXT | True |  |  |
| memberid | TEXT | True |  |  |
| start_date | TEXT | True |  |  |
| end_date | TEXT | True |  |  |
| payer | TEXT | True |  |  |
| secondary_payer | TEXT | True |  |  |
| plan_ownership | TEXT | True |  |  |
| owner_name | TEXT | True |  |  |


### Claims_Transactions
**Rows**: 0
**Primary Key**: None

#### Columns
| Column | Type | Nullable | Default | Constraints |
|--------|------|----------|---------|-------------|
| id | TEXT | True |  |  |
| claimid | TEXT | True |  |  |
| chargeid | BIGINT | True |  |  |
| patientid | TEXT | True |  |  |
| type | TEXT | True |  |  |
| amount | DOUBLE PRECISION | True |  |  |
| method | TEXT | True |  |  |
| fromdate | TEXT | True |  |  |
| todate | TEXT | True |  |  |
| placeofservice | TEXT | True |  |  |
| procedurecode | BIGINT | True |  |  |
| modifier1 | DOUBLE PRECISION | True |  |  |
| modifier2 | DOUBLE PRECISION | True |  |  |
| diagnosisref1 | BIGINT | True |  |  |
| diagnosisref2 | DOUBLE PRECISION | True |  |  |
| diagnosisref3 | DOUBLE PRECISION | True |  |  |
| diagnosisref4 | DOUBLE PRECISION | True |  |  |
| units | BIGINT | True |  |  |
| departmentid | BIGINT | True |  |  |
| notes | TEXT | True |  |  |
| unitamount | DOUBLE PRECISION | True |  |  |
| transferoutid | DOUBLE PRECISION | True |  |  |
| transfertype | TEXT | True |  |  |
| payments | DOUBLE PRECISION | True |  |  |
| adjustments | DOUBLE PRECISION | True |  |  |
| transfers | DOUBLE PRECISION | True |  |  |
| outstanding | DOUBLE PRECISION | True |  |  |
| appointmentid | TEXT | True |  |  |
| linenote | DOUBLE PRECISION | True |  |  |
| patientinsuranceid | TEXT | True |  |  |
| feescheduleid | BIGINT | True |  |  |
| providerid | TEXT | True |  |  |
| supervisingproviderid | TEXT | True |  |  |


## Relationship Matrix

| From Table | From Column | To Table | To Column | Constraint |
|------------|-------------|----------|-----------|------------|
| providers | organization_id | organizations | id | providers_organization_id_fkey |
| encounters | organization_id | organizations | id | encounters_organization_id_fkey |
| encounters | patient_id | patients | id | encounters_patient_id_fkey |
| encounters | payer_id | payers | id | encounters_payer_id_fkey |
| encounters | provider_id | providers | id | encounters_provider_id_fkey |
| care_plans | encounter_id | encounters | id | care_plans_encounter_id_fkey |
| care_plans | patient_id | patients | id | care_plans_patient_id_fkey |
| conditions | encounter_id | encounters | id | conditions_encounter_id_fkey |
| conditions | patient_id | patients | id | conditions_patient_id_fkey |
| medications | encounter_id | encounters | id | medications_encounter_id_fkey |
| medications | patient_id | patients | id | medications_patient_id_fkey |
| medications | payer_id | payers | id | medications_payer_id_fkey |
| claims | patient_id | patients | id | claims_patient_id_fkey |
| claims | provider_id | providers | id | claims_provider_id_fkey |

## Database Views

- `patient_summary`
- `recent_encounters`
- `active_conditions`
- `current_medications`

## Data Quality Insights

- **Total Records**: 117,440
- **Populated Tables**: 10/12
- **Database Size**: Estimated based on row counts
