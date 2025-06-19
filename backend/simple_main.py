from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import json

app = FastAPI(title="Text-to-SQL RAG System (Demo Mode)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    database_context: Optional[str] = None
    include_explanation: bool = True
    max_results: int = 100

class QueryResponse(BaseModel):
    sql_query: str
    results: List[Dict[str, Any]]
    explanation: str
    confidence_score: float
    execution_time: float
    metadata: Dict[str, Any]

# Sample data
sample_employees = [
    {"id": 1, "first_name": "John", "last_name": "Doe", "email": "john.doe@company.com", "department": "Engineering", "salary": 95000, "hire_date": "2022-01-15"},
    {"id": 2, "first_name": "Jane", "last_name": "Smith", "email": "jane.smith@company.com", "department": "Sales", "salary": 75000, "hire_date": "2021-03-20"},
    {"id": 3, "first_name": "Bob", "last_name": "Johnson", "email": "bob.johnson@company.com", "department": "Engineering", "salary": 105000, "hire_date": "2020-06-10"},
    {"id": 4, "first_name": "Alice", "last_name": "Williams", "email": "alice.williams@company.com", "department": "Marketing", "salary": 65000, "hire_date": "2023-02-01"},
    {"id": 5, "first_name": "Charlie", "last_name": "Brown", "email": "charlie.brown@company.com", "department": "HR", "salary": 70000, "hire_date": "2021-11-30"},
]

sample_schema = {
    "employees": {
        "columns": [
            {"name": "id", "type": "INTEGER", "nullable": False, "default": None},
            {"name": "first_name", "type": "VARCHAR(50)", "nullable": False, "default": None},
            {"name": "last_name", "type": "VARCHAR(50)", "nullable": False, "default": None},
            {"name": "email", "type": "VARCHAR(100)", "nullable": False, "default": None},
            {"name": "department", "type": "VARCHAR(50)", "nullable": True, "default": None},
            {"name": "salary", "type": "DECIMAL(10,2)", "nullable": True, "default": None},
            {"name": "hire_date", "type": "DATE", "nullable": True, "default": None},
        ],
        "sample_data": sample_employees[:3]
    },
    "departments": {
        "columns": [
            {"name": "id", "type": "INTEGER", "nullable": False, "default": None},
            {"name": "name", "type": "VARCHAR(50)", "nullable": False, "default": None},
            {"name": "budget", "type": "DECIMAL(12,2)", "nullable": True, "default": None},
            {"name": "location", "type": "VARCHAR(100)", "nullable": True, "default": None},
        ],
        "sample_data": [
            {"id": 1, "name": "Engineering", "budget": 500000, "location": "San Francisco"},
            {"id": 2, "name": "Sales", "budget": 300000, "location": "New York"},
            {"id": 3, "name": "Marketing", "budget": 200000, "location": "Los Angeles"},
        ]
    }
}

def generate_mock_response(question: str) -> QueryResponse:
    """Generate a mock response for demonstration purposes"""
    start_time = time.time()
    
    # Simple keyword-based query generation
    if "engineering" in question.lower():
        sql_query = "SELECT * FROM employees WHERE department = 'Engineering'"
        results = [emp for emp in sample_employees if emp["department"] == "Engineering"]
        explanation = "This query filters employees by the Engineering department using a WHERE clause."
    elif "salary" in question.lower() and "average" in question.lower():
        sql_query = "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department"
        dept_salaries = {}
        for emp in sample_employees:
            dept = emp["department"]
            if dept not in dept_salaries:
                dept_salaries[dept] = []
            dept_salaries[dept].append(emp["salary"])
        
        results = [
            {"department": dept, "avg_salary": sum(salaries) / len(salaries)}
            for dept, salaries in dept_salaries.items()
        ]
        explanation = "This query calculates the average salary for each department using GROUP BY and AVG aggregate function."
    elif "top" in question.lower() and "salary" in question.lower():
        sql_query = "SELECT * FROM employees ORDER BY salary DESC LIMIT 5"
        results = sorted(sample_employees, key=lambda x: x["salary"], reverse=True)[:5]
        explanation = "This query sorts employees by salary in descending order and limits results to top 5."
    else:
        sql_query = "SELECT * FROM employees"
        results = sample_employees
        explanation = "This query retrieves all employee records from the database."
    
    execution_time = time.time() - start_time
    
    return QueryResponse(
        sql_query=sql_query,
        results=results,
        explanation=explanation,
        confidence_score=0.85,
        execution_time=execution_time,
        metadata={
            "complexity": "simple",
            "validation_passed": True,
            "optimization_applied": False,
            "retry_count": 0
        }
    )

@app.get("/")
async def root():
    return {"message": "Text-to-SQL RAG System (Demo Mode) is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "components": {
            "database": True,
            "rag_system": True,
            "workflow": True
        }
    }

@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    try:
        return generate_mock_response(request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema")
async def get_database_schema():
    return {"schema": sample_schema}

@app.get("/tables")
async def get_tables():
    return {"tables": list(sample_schema.keys())}

@app.get("/query-history")
async def get_query_history(limit: int = 50):
    # Mock history data
    history = [
        {
            "id": 1,
            "question": "Show all employees in engineering",
            "sql_query": "SELECT * FROM employees WHERE department = 'Engineering'",
            "results_count": 2,
            "execution_time": 0.156,
            "confidence_score": 0.9,
            "created_at": "2024-01-15T10:30:00",
            "success": True,
            "metadata": {"complexity": "simple"}
        },
        {
            "id": 2,
            "question": "What is the average salary by department?",
            "sql_query": "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department",
            "results_count": 4,
            "execution_time": 0.234,
            "confidence_score": 0.85,
            "created_at": "2024-01-15T10:25:00",
            "success": True,
            "metadata": {"complexity": "medium"}
        }
    ]
    return {"history": history}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)