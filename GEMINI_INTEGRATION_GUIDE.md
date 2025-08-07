# 🤖 Gemini LLM Integration Guide

## 🎉 **Complete Gemini Integration with RAG System**

Your Clinical NLQ Assistant now supports **Google Gemini LLM** alongside the existing T5 model, providing multiple AI-powered approaches for SQL generation.

## 🚀 **What's New**

### ✅ **Gemini LLM Client**
- **Direct integration** with Google Gemini API
- **Query enhancement** using Gemini's advanced language understanding
- **Direct SQL generation** as an alternative to T5
- **Intelligent fallback** between different LLM approaches

### ✅ **Enhanced RAG System**
- **Multi-LLM support**: Choose between Gemini, OpenAI, or none
- **Hybrid approaches**: Combine multiple AI models for best results
- **Configurable preferences**: Set your preferred LLM in config

### ✅ **REST API Server**
- **FastAPI-based** REST API for programmatic access
- **Multiple endpoints** for different use cases
- **Comprehensive documentation** with Swagger UI
- **Health monitoring** and statistics

### ✅ **Updated Streamlit Interface**
- **LLM selection controls** in the sidebar
- **SQL generation method** selection (T5, Gemini, Hybrid)
- **Enhanced result display** showing which AI was used
- **Real-time performance metrics**

## 🔧 **Setup Instructions**

### 1. **Install Dependencies**
```bash
# Install Gemini and API dependencies
pip install google-generativeai fastapi uvicorn[standard]

# Or install all at once
pip install -r requirements_api.txt
```

### 2. **Get Gemini API Key**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Set environment variable:
```bash
# Windows
set GEMINI_API_KEY=your_api_key_here

# Linux/Mac
export GEMINI_API_KEY=your_api_key_here
```

### 3. **Update Configuration**
The system automatically detects Gemini availability. You can configure preferences in `config/config.yaml`:

```yaml
rag:
  enabled: true
  preferred_llm: "gemini"  # gemini, openai, none
  
  gemini:
    model_name: "gemini-1.5-flash"
    temperature: 0.1
    api_key: "${GEMINI_API_KEY}"
```

## 🎮 **Usage Options**

### **Option 1: Enhanced Streamlit App** ⭐ **RECOMMENDED**
```bash
streamlit run src/ui/streamlit_app.py
```

**New Features:**
- 🧠 **LLM Selection**: Choose Gemini, OpenAI, or none
- 🔧 **SQL Method**: T5 Enhanced, Gemini Direct, or Hybrid
- 📊 **Enhanced Results**: See which AI generated your SQL
- 🎯 **Performance Metrics**: Real-time success rates and timing

### **Option 2: REST API Server**
```bash
# Start the API server
python start_gemini_api.py

# Or with custom settings
python start_gemini_api.py --host 0.0.0.0 --port 8000 --reload
```

**API Endpoints:**
- `POST /query` - Process natural language queries
- `GET /health` - Health check and service status
- `GET /stats` - Performance statistics
- `POST /enhance` - Query enhancement only
- `GET /examples/{query}` - Get similar training examples

**API Documentation:** http://localhost:8000/docs

### **Option 3: Direct Python Integration**
```python
from src.nlq.rag_inference_engine import RAGEnhancedInferenceEngine

# Initialize engine with Gemini support
engine = RAGEnhancedInferenceEngine()
engine.load_model()
engine.initialize_rag_system()

# Generate SQL with Gemini
result = engine.generate_sql_with_gemini(
    "Show me patients with diabetes",
    use_rag=True
)

print(f"SQL: {result['generated_sql']}")
print(f"Method: {result['metadata']['method']}")
```

## 🔍 **SQL Generation Methods**

### **1. T5 Model (Enhanced)** - *Default*
- Uses your trained T5 model
- Enhanced with RAG-retrieved examples
- Consistent with your training data
- **Best for**: Domain-specific queries, consistent formatting

### **2. Gemini Direct** - *New*
- Uses Google Gemini LLM directly
- Leverages Gemini's advanced language understanding
- Enhanced with RAG examples for context
- **Best for**: Complex queries, natural language understanding

### **3. Hybrid Approach** - *Smart*
- Tries Gemini first for advanced understanding
- Falls back to T5 if Gemini fails or produces invalid SQL
- Combines strengths of both approaches
- **Best for**: Maximum reliability and coverage

## 📊 **Performance Comparison**

| Method | Speed | Accuracy | Complexity Handling | Consistency |
|--------|-------|----------|-------------------|-------------|
| T5 Enhanced | ⚡⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Gemini Direct | ⚡⚡ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Hybrid | ⚡⚡ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 🧪 **Testing Your Integration**

### **Quick Test**
```bash
python test_gemini_integration.py
```

This comprehensive test will verify:
- ✅ Gemini client initialization
- ✅ RAG-Gemini integration
- ✅ Inference engine with multiple methods
- ✅ API server functionality (if running)

### **API Client Test**
```bash
# Start API server first
python start_gemini_api.py

# In another terminal, test the API
python src/api/api_client.py
```

## 🌐 **API Usage Examples**

### **cURL Examples**
```bash
# Health check
curl http://localhost:8000/health

# Process query with Gemini
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me patients with diabetes",
    "method": "gemini_direct",
    "use_rag": true
  }'

# Get statistics
curl http://localhost:8000/stats
```

### **Python Client**
```python
from src.api.api_client import GeminiRAGAPIClient

client = GeminiRAGAPIClient("http://localhost:8000")

# Process query
result = client.query(
    "How many patients are there?",
    method="hybrid",
    use_rag=True
)

print(f"Success: {result.success}")
print(f"SQL: {result.generated_sql}")
print(f"Method: {result.method_used}")
```

## 🔧 **Configuration Options**

### **Environment Variables**
```bash
# Required for Gemini
GEMINI_API_KEY=your_gemini_api_key

# Optional: Alternative name
GOOGLE_API_KEY=your_gemini_api_key

# Optional: OpenAI fallback
OPENAI_API_KEY=your_openai_api_key

# Database (existing)
DB_HOST=localhost
DB_NAME=clinical_data
DB_USERNAME=your_username
DB_PASSWORD=your_password
DB_SCHEMA=public
```

### **Config File Settings**
```yaml
# config/config.yaml
rag:
  enabled: true
  preferred_llm: "gemini"  # gemini, openai, none
  similarity_threshold: 0.7
  top_k_examples: 5
  
  gemini:
    model_name: "gemini-1.5-flash"  # or gemini-1.5-pro
    temperature: 0.1
    top_p: 0.8
    max_output_tokens: 2048
```

## 🎯 **Use Cases**

### **When to Use Gemini Direct**
- ✅ Complex natural language queries
- ✅ Queries requiring deep understanding
- ✅ When you want the latest AI capabilities
- ✅ Exploratory data analysis

### **When to Use T5 Enhanced**
- ✅ Domain-specific medical queries
- ✅ When consistency is critical
- ✅ Offline or air-gapped environments
- ✅ Cost-sensitive applications

### **When to Use Hybrid**
- ✅ Production environments requiring reliability
- ✅ When you want best of both worlds
- ✅ Critical applications needing fallbacks
- ✅ Maximum query coverage

## 🚨 **Troubleshooting**

### **Common Issues**

#### **"Gemini not available"**
- ✅ Check `GEMINI_API_KEY` environment variable
- ✅ Verify internet connection
- ✅ Ensure `google-generativeai` is installed

#### **"API key invalid"**
- ✅ Verify API key is correct
- ✅ Check API key permissions
- ✅ Ensure billing is enabled (if required)

#### **"Model loading failed"**
- ✅ Check model path in config
- ✅ Verify T5 model files exist
- ✅ Ensure sufficient memory

#### **"RAG system not initialized"**
- ✅ Check training data path
- ✅ Verify sentence-transformers installation
- ✅ Ensure training data format is correct

### **Debug Mode**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python test_gemini_integration.py
```

## 📈 **Performance Optimization**

### **For Speed**
- Use `gemini-1.5-flash` model (faster)
- Reduce `top_k_examples` in RAG
- Cache embeddings
- Use T5 for simple queries

### **For Accuracy**
- Use `gemini-1.5-pro` model (more capable)
- Increase `top_k_examples` in RAG
- Use hybrid approach
- Fine-tune temperature settings

### **For Cost**
- Prefer T5 model when possible
- Use Gemini only for complex queries
- Implement query caching
- Monitor API usage

## 🔮 **Future Enhancements**

### **Planned Features**
- 🔄 **Model switching** based on query complexity
- 📊 **Advanced analytics** and query insights
- 🎯 **Query optimization** suggestions
- 🔐 **Enhanced security** and access control
- 📱 **Mobile API** support
- 🌍 **Multi-language** support

### **Integration Possibilities**
- **Claude AI** integration
- **Azure OpenAI** support
- **Custom model** fine-tuning
- **Vector database** integration
- **Real-time learning** from user feedback

## 🎊 **Summary**

Your Clinical NLQ Assistant now features:

### ✅ **Multi-AI Architecture**
- **Google Gemini** for advanced language understanding
- **T5 Model** for domain-specific consistency
- **Hybrid approaches** for maximum reliability

### ✅ **Flexible Deployment**
- **Streamlit app** for interactive use
- **REST API** for programmatic access
- **Python library** for direct integration

### ✅ **Production Ready**
- **Comprehensive testing** suite
- **Health monitoring** and metrics
- **Error handling** and fallbacks
- **Detailed documentation**

---

## 🚀 **Get Started Now!**

```bash
# 1. Set your API key
set GEMINI_API_KEY=your_api_key_here

# 2. Test the integration
python test_gemini_integration.py

# 3. Start the enhanced app
streamlit run src/ui/streamlit_app.py

# 4. Or start the API server
python start_gemini_api.py
```

**🎉 Your Clinical NLQ Assistant is now powered by cutting-edge AI technology!**