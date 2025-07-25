# NLQ Query Performance Test Report
*Generated on: 2025-07-25 22:42:22*

## Executive Summary
- **Total Queries Tested**: 10
- **Success Rate**: 90.0%
- **Average Execution Time**: 0.0045s
- **Queries Meeting Performance Expectations**: 100.0%
- **Total Rows Returned**: 480

## Query Performance by Category

| Category | Queries | Avg Time (s) | Success Rate | Total Rows |
|----------|---------|--------------|--------------|------------|
| basic_count | 1 | 0.0 | 100.0% | 1 |
| basic_filter | 1 | 0.0 | 100.0% | 44 |
| aggregation | 1 | 0.0 | 100.0% | 10 |
| join_filter | 1 | 0.0 | 100.0% | 38 |
| join_aggregation | 1 | 0.0047 | 100.0% | 107 |
| medication_analysis | 1 | 0.0 | 100.0% | 3 |
| complex_aggregation | 1 | 0.002 | 100.0% | 10 |
| complex_clinical | 1 | 0.0259 | 100.0% | 27 |
| financial_analysis | 1 | 0.0081 | 100.0% | 240 |

## Detailed Query Results

### query_1_basic_count
**Natural Language**: How many patients do we have?
**Status**: ✅ **Performance**: 🚀
**Execution Time**: 0.0s
**Rows Returned**: 1
**Category**: basic_count

### query_2_basic_filter
**Natural Language**: Show me all female patients
**Status**: ✅ **Performance**: 🚀
**Execution Time**: 0.0s
**Rows Returned**: 44
**Category**: basic_filter

### query_3_aggregation
**Natural Language**: What are the most common conditions?
**Status**: ✅ **Performance**: 🚀
**Execution Time**: 0.0s
**Rows Returned**: 10
**Category**: aggregation

### query_4_join_filter
**Natural Language**: Show patients with diabetes
**Status**: ✅ **Performance**: 🚀
**Execution Time**: 0.0s
**Rows Returned**: 38
**Category**: join_filter

### query_5_join_aggregation
**Natural Language**: How many encounters did each patient have?
**Status**: ✅ **Performance**: 🚀
**Execution Time**: 0.0047s
**Rows Returned**: 107
**Category**: join_aggregation

### query_6_medication_analysis
**Natural Language**: What medications are prescribed for hypertension?
**Status**: ✅ **Performance**: 🚀
**Execution Time**: 0.0s
**Rows Returned**: 3
**Category**: medication_analysis

### query_7_complex_aggregation
**Natural Language**: Show patient demographics by age group
**Status**: ✅ **Performance**: 🚀
**Execution Time**: 0.002s
**Rows Returned**: 10
**Category**: complex_aggregation

### query_8_complex_clinical
**Natural Language**: Find patients with multiple chronic conditions
**Status**: ✅ **Performance**: 🚀
**Execution Time**: 0.0259s
**Rows Returned**: 27
**Category**: complex_clinical

### query_9_financial_analysis
**Natural Language**: What's the average cost per encounter by organization?
**Status**: ✅ **Performance**: 🚀
**Execution Time**: 0.0081s
**Rows Returned**: 240
**Category**: financial_analysis

### query_10_temporal_analysis
**Natural Language**: Show medication adherence patterns
**Status**: ❌ **Performance**: ⚠️
**Execution Time**: Nones
**Rows Returned**: 0
**Category**: temporal_analysis

## Database Insights

### Patient Demographics
- **Total Patients**: 107
- **Female Patients**: 44
- **Male Patients**: 63
- **Female Percentage**: 41.1
- **Male Percentage**: 58.9
- **Average Age**: 41.0
- **Age Range**: 1925-09-07 to 2024-08-29