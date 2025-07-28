# 🔄 Model Comparison Report

## 📊 Performance Summary

| Metric | Previous Model | Current Model | Improvement |
|--------|----------------|---------------|-------------|
| **Validity Rate** | 100.0% | 80.0% | -20.0% |
| **Syntax Correctness** | 0.0% | 10.0% | +10.0% |
| **Schema Compliance** | 0.0% | 0.0% | +0.0% |
| **Avg Generation Time** | 1.013s | 2.180s | -1.168s |

## 🎯 Overall Assessment

📉 **SIGNIFICANT REGRESSION** - Current model is much worse

## 🔍 Detailed Analysis

### Model Loading
- **Previous Model**: Loaded in 0.55s
- **Current Model**: Loaded in 0.37s
- **Model Size**: 60,506,624 parameters

### Query-by-Query Comparison

#### Query 1: How many patients do we have?

**Previous Model Output:**
```sql
SELECT COUNT(*) as patients?
```

**Current Model Output:**
```sql
SELECT HOW MANY PATIENTS DO WE HAVE?
```

❌ **REGRESSION**: Previous model was better

---

#### Query 2: Show me all male patients

**Previous Model Output:**
```sql
SELECT MANY
```

**Current Model Output:**
```sql
SELECT MANY MANY MANY MANY MANY MANY MANY MANY PATIENTS.
```

❌ **REGRESSION**: Previous model was better

---

#### Query 3: Find all patients with diabetes

**Previous Model Output:**
```sql
SELECT DISTINCT CURRENT
```

**Current Model Output:**
```sql
SELECT DISTINCT p.
```

✅ **BOTH VALID**: Both models generate valid SQL

---

#### Query 4: What are the most common conditions?

**Previous Model Output:**
```sql
SELECT DISTINCT DISTINCT
```

**Current Model Output:**
```sql
SELECT WHICH ARE THE MOST COMMON CONDITIONS?
```

✅ **BOTH VALID**: Both models generate valid SQL

---

#### Query 5: Which providers see the most patients?

**Previous Model Output:**
```sql
SELECT DISTINCT DISTINCT
```

**Current Model Output:**
```sql
SELECT which providers see the most patients?
```

✅ **BOTH VALID**: Both models generate valid SQL

---

#### Query 6: Find patients with both diabetes and hypertension

**Previous Model Output:**
```sql
SELECT patients with diabetes and hypertension
```

**Current Model Output:**
```sql
SELECT sowohl Diabetes als auch Hypertension als Symptome.
```

✅ **BOTH VALID**: Both models generate valid SQL

---

#### Query 7: What is the average cost per encounter?

**Previous Model Output:**
```sql
SELECT COUNT(*) as average cost per encounter?
```

**Current Model Output:**
```sql
SELECT WHERE IST DER durchschnittliche Aufwand pro Begegnung?
```

✅ **BOTH VALID**: Both models generate valid SQL

---

#### Query 8: Show patients diagnosed in the last year

**Previous Model Output:**
```sql
SELECT p.l.
```

**Current Model Output:**
```sql
SELECT PILOTS FROM SELECTING PERSONAL PILOTS FROM THE CURRENT YEAR.
```

✅ **BOTH VALID**: Both models generate valid SQL

---

#### Query 9: List all medications for patient ID 123

**Previous Model Output:**
```sql
SELECT p.l.
```

**Current Model Output:**
```sql
SELECT sämtliche Medikamente für den Patienten ID 123 auf.
```

✅ **BOTH VALID**: Both models generate valid SQL

---

#### Query 10: Find encounters with high costs

**Previous Model Output:**
```sql
SELECT a high cost
```

**Current Model Output:**
```sql
SELECT eXTRACTS mit hohen Kosten.
```

✅ **BOTH VALID**: Both models generate valid SQL

---

## 🎯 Recommendations

⚠️ **Revert to Previous Model**: Current model shows significant regression

**Generated on**: 2025-07-28 17:41:22
