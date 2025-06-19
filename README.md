# 🧠 Advanced Text-to-SQL RAG System

A sophisticated Text-to-SQL system built with **LangChain**, **LangGraph**, and modern web technologies. This system converts natural language questions into SQL queries using Retrieval-Augmented Generation (RAG) with advanced features like self-correction, query optimization, and real-time execution.

![image](https://github.com/user-attachments/assets/ff18dce0-097e-4b40-b7ba-8114e63a1f0e)

## ✨ Features

### 🔍 Advanced RAG System
- **Vector embeddings** for schema understanding and query examples
- **Semantic search** for relevant context retrieval
- **Example-based learning** with curated query patterns
- **Schema-aware** query generation

### 🚀 LangGraph Workflow
- **Multi-step workflow** with validation and self-correction
- **Automatic retry logic** for failed queries
- **Query optimization** and performance tuning
- **Real-time progress tracking** via WebSocket

### 🛡️ Security & Validation
- **SQL injection prevention** with comprehensive validation
- **Query complexity analysis** and safety checks
- **Execution sandboxing** with result limits
- **Error handling** and user feedback

### 🎨 Modern UI/UX
- **Dark theme** with Material-UI components
- **Real-time query execution** with progress indicators
- **Interactive data visualization** with charts
- **Monaco Editor** for SQL syntax highlighting
- **Responsive design** for all devices

### 📊 Analytics & Monitoring
- **Query history** tracking and analysis
- **Performance metrics** and success rates
- **Error analysis** and debugging tools
- **Database schema explorer**

## 🏗️ Architecture

```
├── backend/                 # FastAPI Backend
│   ├── main.py             # Application entry point
│   ├── database/           # Database management
│   ├── rag/               # RAG system implementation
│   ├── graph/             # LangGraph workflow
│   └── utils/             # Utilities and validators
├── frontend/              # React Frontend
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom hooks
│   │   └── utils/         # API and utilities
└── requirements.txt       # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- OpenAI API key
- PostgreSQL (optional, SQLite by default)

### Backend Setup

1. **Install dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set environment variables**:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key and database settings
```

3. **Run the backend**:
```bash
cd backend
python main.py
```

The backend will start at `http://localhost:8001`

### Frontend Setup

1. **Install dependencies**:
```bash
cd frontend
npm install
```

2. **Start the development server**:
```bash
npm start
```

The frontend will start at `http://localhost:3000`

## 🎯 Usage Examples

### Basic Queries
- "Show all employees in the engineering department"
- "What is the average salary by department?"
- "List all active projects"

### Complex Analytics
- "Show top 5 highest paid employees with their department info"
- "Find employees working on multiple active projects"
- "Compare sales performance by region for this year"

### Advanced Patterns
- "Which departments have budget exceeding the average?"
- "Show project timeline with employee assignments"
- "Analyze salary distribution across departments"

## 🔧 Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/texttosql_db
REDIS_URL=redis://localhost:6379
CHROMA_PERSIST_DIRECTORY=./chroma_db
LOG_LEVEL=INFO
MAX_QUERY_COMPLEXITY=10
QUERY_TIMEOUT_SECONDS=30
ENABLE_QUERY_CACHING=true
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Database Configuration
The system supports both SQLite (default) and PostgreSQL:

- **SQLite**: Zero configuration, perfect for development
- **PostgreSQL**: Production-ready with advanced features

## 📊 Sample Data

The system includes a comprehensive sample database with:
- **Employees** table with HR data
- **Departments** with budget information
- **Projects** with timeline and status
- **Sales** data with regional breakdown
- **Relationships** between entities

## 🛠️ Advanced Features

### RAG System
- **Embedding-based retrieval** using Sentence Transformers
- **Context-aware** query generation
- **Few-shot learning** with example queries
- **Schema documentation** integration

### LangGraph Workflow
```python
retrieve_context → generate_sql → validate_sql → optimize_query → execute_query
                    ↓              ↓             ↓
                  retry_logic → error_handling → result_processing
```

### Query Optimization
- **Automatic LIMIT** addition for performance
- **Index suggestion** based on query patterns
- **Redundant condition** removal
- **Join optimization** hints

### Security Measures
- **Whitelist-based** SQL validation
- **Injection attack** prevention
- **Query complexity** limits
- **Execution timeout** controls

## 🔍 API Documentation

### Core Endpoints
- `GET /health` - System health check
- `POST /query` - Execute natural language query
- `GET /schema` - Database schema information
- `GET /tables` - List all tables
- `GET /query-history` - Query execution history
- `WS /ws/query` - Real-time query execution

### Example Request
```json
POST /query
{
  "question": "Show top 5 employees by salary",
  "include_explanation": true,
  "max_results": 100
}
```

### Example Response
```json
{
  "sql_query": "SELECT * FROM employees ORDER BY salary DESC LIMIT 5",
  "results": [...],
  "explanation": "This query selects all columns from the employees table...",
  "confidence_score": 0.95,
  "execution_time": 0.123,
  "metadata": {
    "complexity": "simple",
    "validation_passed": true,
    "optimization_applied": true
  }
}
```

## 🎨 UI Components

### Query Interface
- **Natural language input** with autocomplete
- **Real-time execution** with progress tracking
- **Result visualization** with charts and tables
- **SQL query display** with syntax highlighting

### Schema Explorer
- **Interactive table browser**
- **Column details** with types and constraints
- **Sample data preview**
- **Relationship visualization**

### Analytics Dashboard
- **Query performance** metrics
- **Success rate** tracking
- **Error analysis** and debugging
- **Usage patterns** and trends

## 🚀 Advanced Suggestions

### 1. **Custom Schema Integration**
```python
# Add your own database schema
await db_manager.add_custom_schema({
    "your_table": {
        "columns": [...],
        "relationships": [...],
        "sample_queries": [...]
    }
})
```

### 2. **Extend RAG Context**
```python
# Add domain-specific examples
rag_system.add_examples([
    {
        "question": "Your domain question",
        "sql": "SELECT ...",
        "explanation": "Domain-specific explanation"
    }
])
```

### 3. **Custom Validators**
```python
# Add business logic validation
class CustomValidator(SQLValidator):
    def validate_business_rules(self, query):
        # Your custom validation logic
        pass
```

### 4. **Performance Monitoring**
```python
# Add custom metrics
@app.middleware("http")
async def add_metrics(request, call_next):
    # Custom monitoring logic
    pass
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangChain** for the RAG framework
- **LangGraph** for workflow orchestration
- **OpenAI** for language model capabilities
- **Material-UI** for the beautiful interface
- **FastAPI** for the high-performance backend

---

Built with ❤️ for the AI and Data Science community
