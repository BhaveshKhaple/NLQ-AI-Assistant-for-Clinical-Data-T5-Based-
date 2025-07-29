# 🏥 Clinical NLQ Assistant - Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- Windows 10/11
- Python 3.10+ installed
- PostgreSQL database (optional for basic testing)

### 1. Launch the Application

Choose any of these methods:

#### Option A: Double-click the batch file
```
Double-click: start_app.bat
```

#### Option B: Use PowerShell
```powershell
.\start_app.ps1
```

#### Option C: Command line
```bash
streamlit run app.py
```

### 2. Access the Application
- Open your web browser
- Go to: **http://localhost:8501**
- The application will load automatically

## 💡 How to Use

### Basic Query Examples
Try these sample queries:

```
How many patients do we have?
Show me all male patients
Find patients with diabetes
List all providers
What medications are most commonly prescribed?
Show patients over 65 years old
Find patients from Boston
Which provider sees the most patients?
```

### Advanced Queries
```
Show patients with multiple chronic conditions
Find patients taking insulin and metformin
What is the average age of diabetic patients?
Show recent patient visits this month
List patients with high blood pressure medication
```

## 🔧 Features

### 📊 Query Results
- **Table View**: Sortable and filterable data tables
- **Export Options**: Download as CSV, JSON, or Excel
- **Summary Statistics**: Automatic data summaries
- **Visualizations**: Charts and graphs for numeric data

### ⚙️ Settings
- **Output Format**: Choose how results are displayed
- **Query History**: View your previous queries
- **Performance Metrics**: See query processing times
- **Error Recovery**: Get help when queries fail

### 📈 Analytics Dashboard
- **Session Statistics**: Track your usage patterns
- **Query Performance**: Monitor response times
- **Success Rates**: See how well queries are processed
- **Usage Trends**: Analyze your query patterns over time

## 🆘 Troubleshooting

### Application Won't Start
1. Check if Python is installed: `python --version`
2. Ensure virtual environment is activated
3. Try running: `pip install -r requirements.txt`
4. Use a different port: `streamlit run app.py --server.port 8502`

### Database Connection Issues
- The application works without a database for testing
- SQL queries will be generated but not executed
- For full functionality, ensure PostgreSQL is running

### Slow Performance
- First query may take longer (model loading)
- Subsequent queries should be faster
- Check your internet connection for model downloads

### Query Not Working
- Try simpler queries first
- Check the error message for guidance
- Use the suggested query examples
- Review the query history for successful patterns

## 📞 Support

### Getting Help
1. **Error Messages**: Read the detailed error descriptions
2. **Query Suggestions**: Use the built-in query examples
3. **Documentation**: Check the full documentation files
4. **Logs**: Review the application logs for detailed information

### Common Issues
- **Port in use**: Try a different port number
- **Model loading**: Wait for initial model download
- **Database errors**: Expected if PostgreSQL not configured
- **Memory issues**: Close other applications if needed

## 🎯 Best Practices

### Writing Good Queries
- Be specific about what you want to find
- Use medical terminology when appropriate
- Start with simple queries and build complexity
- Review successful queries for patterns

### Performance Tips
- Keep queries focused and specific
- Use filters to limit result sets
- Export large datasets rather than viewing in browser
- Close unused browser tabs to free memory

## 🔒 Privacy & Security

### Data Protection
- All queries are logged for analysis
- No patient data is stored permanently
- Sessions are isolated between users
- Database connections are encrypted

### Session Management
- Each browser session is independent
- Query history is session-specific
- Sessions expire after inactivity
- No personal information is required

---

## 🎉 You're Ready!

The Clinical NLQ Assistant is now ready to help you query clinical data using natural language. Start with simple queries and explore the powerful features as you become more comfortable with the system.

**Happy Querying!** 🏥✨