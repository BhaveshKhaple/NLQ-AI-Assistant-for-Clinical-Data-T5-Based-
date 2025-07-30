# 🗄️ Database Explorer Feature

## Overview

The Database Explorer is a new feature added to the Clinical NLQ Assistant that allows users to explore and understand the database structure before using the natural language query interface. This feature provides comprehensive insights into your clinical database, making it easier to formulate effective natural language queries.

## Features

### 📊 Database Overview
- **Connection Status**: Real-time database connection monitoring
- **Schema Information**: View all available schemas with table counts
- **Database Statistics**: Total tables, columns, and relationships
- **Quick Metrics**: At-a-glance database health indicators

### 🗂️ Table Explorer
- **Table Listing**: Browse all tables in the clinical_data schema
- **Table Metadata**: View table sizes, row counts, and column counts
- **Column Details**: Comprehensive column information including:
  - Data types and constraints
  - Primary keys and foreign keys
  - Nullable fields and default values
  - Column relationships and references
- **Sample Data**: Preview actual data from any table
- **Table Statistics**: Numeric column statistics (min, max, average, distinct counts)

### 🔍 Custom Query Interface
- **SQL Query Editor**: Write and execute custom SQL queries
- **Query Results**: View results in tabular format
- **Export Options**: Download query results as CSV
- **Execution Metrics**: Query execution time tracking
- **Result Limiting**: Control the number of rows returned
- **Quick Statistics**: Automatic statistics for numeric columns

### 🗺️ Schema Diagram
- **Visual Relationships**: Interactive network diagram showing table relationships
- **Foreign Key Mapping**: Visual representation of database constraints
- **Table Sizing**: Node sizes represent table complexity
- **Interactive Exploration**: Hover for detailed table information

### 💡 Query Examples
- **Pre-built Queries**: Ready-to-use example queries for common scenarios
- **Learning Tool**: Understand your data structure through examples
- **One-click Execution**: Run examples directly from the interface

## How to Use

### 1. Access the Database Explorer
1. Launch the Clinical NLQ Assistant: `streamlit run src/ui/streamlit_app.py`
2. Navigate to the **"🗄️ Database Explorer"** tab
3. The system will automatically connect to your configured database

### 2. Explore Your Database Structure

#### Database Overview Tab
- Check connection status and basic database metrics
- Review available schemas and their table counts
- Get a high-level understanding of your database size

#### Tables Tab
- Select any table from the dropdown to explore
- Use the sub-tabs to view different aspects:
  - **📊 Overview**: Basic table information and relationships
  - **📝 Columns**: Detailed column specifications
  - **🔍 Sample Data**: Preview actual table contents
  - **📈 Statistics**: Numeric column analysis

#### Custom Query Tab
- Write SQL queries to explore specific data patterns
- Use the query examples as templates
- Export results for further analysis
- Monitor query performance

#### Schema Diagram Tab
- Visualize table relationships
- Understand foreign key constraints
- Identify central tables in your schema

### 3. Use Insights for NLQ Queries

After exploring your database structure, you can:
- **Understand Available Data**: Know what tables and columns exist
- **Identify Relationships**: Understand how tables connect
- **See Data Patterns**: Preview actual data to understand formats
- **Formulate Better Queries**: Use this knowledge to create more effective natural language queries

## Example Workflow

1. **Start with Overview**: Check database connection and get basic statistics
2. **Explore Key Tables**: Look at `patients`, `conditions`, `medications` tables
3. **Understand Relationships**: See how patient data connects across tables
4. **Preview Sample Data**: Understand data formats and typical values
5. **Try Custom Queries**: Test specific data patterns you're interested in
6. **Switch to NLQ**: Use your understanding to ask better natural language questions

## Sample Queries to Try

### Patient Demographics
```sql
SELECT gender, race, COUNT(*) as patient_count
FROM clinical_data.patients
GROUP BY gender, race
ORDER BY patient_count DESC;
```

### Common Conditions
```sql
SELECT description, COUNT(*) as condition_count
FROM clinical_data.conditions
GROUP BY description
ORDER BY condition_count DESC
LIMIT 10;
```

### Age Distribution
```sql
SELECT 
  CASE 
    WHEN EXTRACT(YEAR FROM AGE(birth_date)) < 18 THEN 'Under 18'
    WHEN EXTRACT(YEAR FROM AGE(birth_date)) BETWEEN 18 AND 65 THEN '18-65'
    ELSE 'Over 65'
  END as age_group,
  COUNT(*) as patient_count
FROM clinical_data.patients
GROUP BY age_group;
```

## Benefits for NLQ Usage

### Better Query Formulation
- **Know Your Data**: Understand what information is available
- **Use Correct Terms**: Reference actual column names and values
- **Understand Relationships**: Ask questions that span related tables appropriately

### Improved Query Success Rate
- **Realistic Expectations**: Know what data exists before asking
- **Proper Terminology**: Use terms that match your database schema
- **Complex Queries**: Understand relationships for multi-table questions

### Data Quality Insights
- **Identify Gaps**: See where data might be missing
- **Understand Formats**: Know how dates, codes, and text are stored
- **Spot Patterns**: Recognize common values and distributions

## Technical Details

### Database Connection
- Uses the same connection configuration as the main NLQ system
- Automatically loads environment variables from `.env` file
- Supports PostgreSQL with the clinical_data schema

### Performance Considerations
- **Caching**: Table metadata is cached for better performance
- **Sampling**: Sample data queries are limited to prevent large data loads
- **Timeouts**: Query execution includes timeout protection
- **Connection Management**: Proper connection cleanup and error handling

### Security
- **Read-Only Access**: Database explorer only performs SELECT operations
- **Query Validation**: Basic SQL injection protection
- **Connection Limits**: Respects database connection pooling

## Troubleshooting

### Connection Issues
- Ensure PostgreSQL is running
- Check database credentials in `.env` file
- Verify the clinical_data schema exists

### Performance Issues
- Reduce sample data size for large tables
- Use query limits for custom queries
- Check database server resources

### Display Issues
- Refresh the browser if visualizations don't load
- Check browser console for JavaScript errors
- Ensure all required Python packages are installed

## Future Enhancements

- **Query History**: Save and reuse custom queries
- **Data Profiling**: Advanced data quality analysis
- **Export Options**: Multiple export formats (JSON, Excel)
- **Query Optimization**: Suggest query improvements
- **Real-time Monitoring**: Live database statistics updates

## Integration with NLQ

The Database Explorer seamlessly integrates with the main NLQ functionality:

1. **Explore First**: Use the Database Explorer to understand your data
2. **Query Second**: Switch to the Query Interface tab with better knowledge
3. **Iterate**: Return to the explorer to understand unexpected results
4. **Refine**: Use insights to improve your natural language queries

This workflow significantly improves the success rate and quality of natural language queries by providing users with the context they need to ask the right questions.