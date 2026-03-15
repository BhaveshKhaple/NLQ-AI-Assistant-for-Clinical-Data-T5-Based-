# Clinical Database Loading Report
*Generated on: 2026-03-13 18:48:30*

## Loading Summary
- **Start Time**: 2026-03-13T18:48:15.492614
- **End Time**: 2026-03-13T18:48:30.241714
- **Duration**: 14.7 seconds
- **Tables Processed**: 9
- **Total Rows Loaded**: 9,859
- **Total Errors**: 1
- **Total Warnings**: 3

## Table Loading Results

| Table | CSV Rows | Loaded Rows | Batches | Success | Duration (s) |
|-------|----------|-------------|---------|---------|--------------|
| organizations | 272 | 272 | 1 | ✅ | 0.2 |
| payers | 10 | 10 | 1 | ✅ | 0.1 |
| patients | 107 | 107 | 1 | ✅ | 0.2 |
| providers | 272 | 272 | 1 | ✅ | 0.2 |
| encounters | 7,217 | 7,217 | 8 | ✅ | 2.2 |
| conditions | 1,438 | 1,000 | 1 | ❌ | 10.9 |
| medications | 854 | 854 | 1 | ✅ | 0.8 |
| procedures | 80 | 80 | 1 | ✅ | 0.1 |
| immunizations | 47 | 47 | 1 | ✅ | 0.1 |

## Errors Encountered

- Failed to load batch 2 after 3 attempts

## Warnings

- CSV file not found: d:\projects\healthca\output\csv\observations.csv
- CSV file not found: d:\projects\healthca\output\csv\allergies.csv
- CSV file not found: d:\projects\healthca\output\csv\care_plans.csv