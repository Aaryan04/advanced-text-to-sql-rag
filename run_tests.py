#!/usr/bin/env python3
"""
Simple test runner to verify backend functionality.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

async def test_sql_validator():
    """Test SQL validation functionality."""
    print("Testing SQL Validator...")
    
    from utils.sql_validator import SQLValidator
    
    validator = SQLValidator()
    sample_tables = ['employees', 'departments', 'projects']
    
    # Test valid query
    result = await validator.validate_query(
        "SELECT * FROM employees WHERE department = 'Engineering'",
        sample_tables
    )
    assert result["is_valid"] is True
    assert len(result["errors"]) == 0
    print("✓ Valid SELECT query test passed")
    
    # Test forbidden DROP
    result = await validator.validate_query("DROP TABLE employees", sample_tables)
    assert result["is_valid"] is False
    assert any("Forbidden keyword: DROP" in error for error in result["errors"])
    print("✓ Forbidden DROP statement test passed")
    
    # Test SQL injection
    result = await validator.validate_query(
        "SELECT * FROM employees; DROP TABLE employees", 
        sample_tables
    )
    assert result["is_valid"] is False
    assert any("Multiple statements are not allowed" in error for error in result["errors"])
    print("✓ SQL injection protection test passed")

async def test_query_optimizer():
    """Test query optimization functionality."""
    print("\nTesting Query Optimizer...")
    
    from utils.query_optimizer import QueryOptimizer
    
    optimizer = QueryOptimizer()
    
    # Test adding LIMIT to SELECT *
    result = await optimizer.optimize_query("SELECT * FROM employees")
    assert result["optimization_applied"] is True
    assert "LIMIT" in result["optimized_query"].upper()
    print("✓ SELECT * LIMIT optimization test passed")
    
    # Test complexity analysis
    simple_analysis = optimizer.analyze_query_complexity("SELECT * FROM employees")
    complex_analysis = optimizer.analyze_query_complexity("""
        SELECT e1.*, e2.*, d.*
        FROM employees e1
        JOIN employees e2 ON e1.manager_id = e2.id
        JOIN departments d ON e1.department = d.name
        WHERE e1.salary > (SELECT AVG(salary) FROM employees)
        GROUP BY e1.department
        HAVING COUNT(*) > 1
    """)
    
    assert complex_analysis["complexity_score"] > simple_analysis["complexity_score"]
    print("✓ Query complexity analysis test passed")

async def test_database_connection():
    """Test database connection functionality."""
    print("\nTesting Database Connection...")
    
    from database.connection import DatabaseManager
    
    # Create a temporary database
    import tempfile
    db_file = tempfile.mktemp(suffix='.db')
    
    try:
        db_manager = DatabaseManager()
        db_manager.database_url = f"sqlite+aiosqlite:///{db_file}"
        await db_manager.initialize()
        
        # Test health check
        health = await db_manager.health_check()
        assert health is True
        print("✓ Database health check passed")
        
        # Test getting tables
        tables = await db_manager.get_all_tables()
        assert isinstance(tables, list)
        assert len(tables) > 0
        print("✓ Get all tables test passed")
        
        # Test simple query
        results = await db_manager.execute_query("SELECT COUNT(*) as count FROM employees")
        assert isinstance(results, list)
        assert len(results) == 1
        assert 'count' in results[0]
        print("✓ Simple query execution test passed")
        
        await db_manager.close()
        
    finally:
        # Clean up
        if os.path.exists(db_file):
            os.unlink(db_file)

async def test_api_endpoints():
    """Test API endpoints using the simple app."""
    print("\nTesting API Endpoints...")
    
    from simple_main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    
    # Test health check
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✓ Health endpoint test passed")
    
    # Test schema endpoint
    response = client.get("/schema")
    assert response.status_code == 200
    schema = response.json()
    assert isinstance(schema, dict)
    assert len(schema) > 0
    print("✓ Schema endpoint test passed")
    
    # Test query endpoint
    response = client.post("/query", json={
        "question": "Show all employees",
        "include_explanation": True,
        "max_results": 10
    })
    assert response.status_code == 200
    result = response.json()
    assert "sql_query" in result
    assert "explanation" in result
    print("✓ Query endpoint test passed")

async def main():
    """Run all tests."""
    print("🚀 Starting Backend API Tests...")
    print("="*50)
    
    try:
        await test_sql_validator()
        await test_query_optimizer()
        await test_database_connection()
        await test_api_endpoints()
        
        print("\n" + "="*50)
        print("🎉 All tests passed successfully!")
        print("✅ Backend APIs are working correctly")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("❌ Backend has issues that need to be resolved")
        return 1
    
    return 0

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(result)