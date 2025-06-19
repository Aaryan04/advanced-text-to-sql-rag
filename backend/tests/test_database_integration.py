import pytest
import asyncio
import tempfile
import os
from pathlib import Path
import sys

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from database.connection import DatabaseManager, QueryHistory


class TestDatabaseManager:
    """Integration tests for DatabaseManager."""
    
    @pytest.mark.asyncio
    async def test_database_initialization(self, test_db_manager):
        """Test that database initializes correctly."""
        assert test_db_manager is not None
        assert test_db_manager.engine is not None
        assert test_db_manager.session_factory is not None
    
    @pytest.mark.asyncio
    async def test_health_check(self, test_db_manager):
        """Test database health check."""
        health = await test_db_manager.health_check()
        assert health is True
    
    @pytest.mark.asyncio
    async def test_get_all_tables(self, test_db_manager):
        """Test retrieving all tables from database."""
        tables = await test_db_manager.get_all_tables()
        assert isinstance(tables, list)
        assert len(tables) > 0
        
        # Should contain our sample tables
        expected_tables = ['employees', 'departments', 'projects', 'employee_projects', 'sales']
        for table in expected_tables:
            assert table in tables
    
    @pytest.mark.asyncio
    async def test_execute_simple_query(self, test_db_manager):
        """Test executing a simple SQL query."""
        sql = "SELECT COUNT(*) as count FROM employees"
        results = await test_db_manager.execute_query(sql)
        
        assert isinstance(results, list)
        assert len(results) == 1
        assert 'count' in results[0]
        assert results[0]['count'] > 0
    
    @pytest.mark.asyncio
    async def test_execute_complex_query(self, test_db_manager):
        """Test executing a complex SQL query with joins."""
        sql = """
        SELECT e.first_name, e.last_name, e.department, e.salary 
        FROM employees e 
        WHERE e.department = 'Engineering' 
        ORDER BY e.salary DESC
        """
        results = await test_db_manager.execute_query(sql)
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Check that all results are from Engineering
        for result in results:
            assert result['department'] == 'Engineering'
        
        # Check that results are ordered by salary (descending)
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i]['salary'] >= results[i + 1]['salary']
    
    @pytest.mark.asyncio
    async def test_execute_query_with_limit(self, test_db_manager):
        """Test executing query with result limit."""
        sql = "SELECT * FROM employees"
        results = await test_db_manager.execute_query(sql, max_results=3)
        
        assert isinstance(results, list)
        assert len(results) <= 3
    
    @pytest.mark.asyncio
    async def test_get_schema_info_all_tables(self, test_db_manager):
        """Test retrieving schema information for all tables."""
        schema = await test_db_manager.get_schema_info()
        
        assert isinstance(schema, dict)
        assert len(schema) > 0
        
        # Check employees table schema
        assert 'employees' in schema
        employees_schema = schema['employees']
        assert 'columns' in employees_schema
        assert 'sample_data' in employees_schema
        
        # Check column structure
        columns = employees_schema['columns']
        column_names = [col['name'] for col in columns]
        expected_columns = ['id', 'first_name', 'last_name', 'email', 'department', 'salary', 'hire_date']
        
        for col in expected_columns:
            assert col in column_names
    
    @pytest.mark.asyncio
    async def test_get_schema_info_specific_table(self, test_db_manager):
        """Test retrieving schema information for specific table."""
        schema = await test_db_manager.get_schema_info(['employees'])
        
        assert isinstance(schema, dict)
        assert 'employees' in schema
        assert len(schema) == 1
        
        employees_schema = schema['employees']
        assert 'columns' in employees_schema
        assert 'sample_data' in employees_schema
    
    @pytest.mark.asyncio
    async def test_save_query_history_success(self, test_db_manager):
        """Test saving successful query to history."""
        await test_db_manager.save_query_history(
            question="Test question",
            sql_query="SELECT * FROM employees",
            results_count=5,
            execution_time=0.123,
            confidence_score=0.95,
            success=True,
            query_metadata={"test": "data"}
        )
        
        # Retrieve history to verify
        history = await test_db_manager.get_query_history(limit=1)
        assert len(history) >= 1
        
        latest_entry = history[0]
        assert latest_entry['question'] == "Test question"
        assert latest_entry['sql_query'] == "SELECT * FROM employees"
        assert latest_entry['results_count'] == 5
        assert latest_entry['success'] is True
    
    @pytest.mark.asyncio
    async def test_save_query_history_failure(self, test_db_manager):
        """Test saving failed query to history."""
        await test_db_manager.save_query_history(
            question="Test failed question",
            sql_query="INVALID SQL",
            results_count=0,
            execution_time=0.0,
            confidence_score=0.0,
            success=False,
            error_message="SQL syntax error"
        )
        
        # Retrieve history to verify
        history = await test_db_manager.get_query_history(limit=10)
        
        # Find our failed entry
        failed_entry = None
        for entry in history:
            if entry['question'] == "Test failed question":
                failed_entry = entry
                break
        
        assert failed_entry is not None
        assert failed_entry['success'] is False
        assert failed_entry['error_message'] == "SQL syntax error"
    
    @pytest.mark.asyncio
    async def test_get_query_history_with_limit(self, test_db_manager):
        """Test retrieving query history with different limits."""
        # Add multiple entries
        for i in range(5):
            await test_db_manager.save_query_history(
                question=f"Test question {i}",
                sql_query=f"SELECT {i}",
                results_count=1,
                execution_time=0.1,
                confidence_score=0.8,
                success=True
            )
        
        # Test different limits
        history_3 = await test_db_manager.get_query_history(limit=3)
        assert len(history_3) <= 3
        
        history_10 = await test_db_manager.get_query_history(limit=10)
        assert len(history_10) <= 10
        assert len(history_10) >= len(history_3)
    
    @pytest.mark.asyncio
    async def test_database_connection_error_handling(self):
        """Test database error handling with invalid connection."""
        db_manager = DatabaseManager()
        db_manager.database_url = "sqlite+aiosqlite:///nonexistent/path/db.sqlite"
        
        # This should handle the error gracefully
        try:
            await db_manager.initialize()
            # If it doesn't raise an error, health check should fail
            health = await db_manager.health_check()
            assert health is False
        except Exception:
            # Exception is expected for invalid path
            pass
        finally:
            await db_manager.close()


class TestDatabaseQueries:
    """Test various database query scenarios."""
    
    @pytest.mark.asyncio
    async def test_employee_department_filter(self, test_db_manager):
        """Test filtering employees by department."""
        sql = "SELECT * FROM employees WHERE department = 'Engineering'"
        results = await test_db_manager.execute_query(sql)
        
        assert len(results) > 0
        for result in results:
            assert result['department'] == 'Engineering'
    
    @pytest.mark.asyncio
    async def test_salary_aggregation(self, test_db_manager):
        """Test salary aggregation queries."""
        sql = "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department"
        results = await test_db_manager.execute_query(sql)
        
        assert len(results) > 0
        for result in results:
            assert 'department' in result
            assert 'avg_salary' in result
            assert result['avg_salary'] > 0
    
    @pytest.mark.asyncio
    async def test_employee_sorting(self, test_db_manager):
        """Test sorting employees by different criteria."""
        sql = "SELECT * FROM employees ORDER BY salary DESC LIMIT 5"
        results = await test_db_manager.execute_query(sql)
        
        assert len(results) <= 5
        # Check descending order
        for i in range(len(results) - 1):
            assert results[i]['salary'] >= results[i + 1]['salary']
    
    @pytest.mark.asyncio
    async def test_join_queries(self, test_db_manager):
        """Test queries with joins between tables."""
        sql = """
        SELECT e.first_name, e.last_name, d.name as dept_name, d.location 
        FROM employees e 
        JOIN departments d ON e.department = d.name 
        LIMIT 5
        """
        results = await test_db_manager.execute_query(sql)
        
        assert len(results) <= 5
        for result in results:
            assert 'first_name' in result
            assert 'last_name' in result
            assert 'dept_name' in result
            assert 'location' in result
    
    @pytest.mark.asyncio
    async def test_date_queries(self, test_db_manager):
        """Test queries involving date operations."""
        sql = "SELECT * FROM employees WHERE hire_date >= '2022-01-01'"
        results = await test_db_manager.execute_query(sql)
        
        assert isinstance(results, list)
        # All results should have hire_date >= 2022-01-01
        for result in results:
            assert result['hire_date'] >= '2022-01-01'
    
    @pytest.mark.asyncio
    async def test_numerical_comparisons(self, test_db_manager):
        """Test queries with numerical comparisons."""
        sql = "SELECT * FROM employees WHERE salary > 80000"
        results = await test_db_manager.execute_query(sql)
        
        assert isinstance(results, list)
        for result in results:
            assert result['salary'] > 80000
    
    @pytest.mark.asyncio
    async def test_count_and_exists(self, test_db_manager):
        """Test COUNT and EXISTS type queries."""
        # Test COUNT
        sql_count = "SELECT COUNT(*) as total FROM employees WHERE is_active = 1"
        count_results = await test_db_manager.execute_query(sql_count)
        
        assert len(count_results) == 1
        assert 'total' in count_results[0]
        assert count_results[0]['total'] >= 0
        
        # Test EXISTS-like query
        sql_exists = "SELECT DISTINCT department FROM employees"
        dept_results = await test_db_manager.execute_query(sql_exists)
        
        assert len(dept_results) > 0
        departments = [row['department'] for row in dept_results]
        assert 'Engineering' in departments


class TestDatabasePerformance:
    """Test database performance and optimization."""
    
    @pytest.mark.asyncio
    async def test_query_execution_time(self, test_db_manager):
        """Test that queries execute within reasonable time."""
        import time
        
        sql = "SELECT * FROM employees"
        
        start_time = time.time()
        results = await test_db_manager.execute_query(sql)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 1.0  # Should complete within 1 second
        assert len(results) > 0
    
    @pytest.mark.asyncio
    async def test_large_result_set_handling(self, test_db_manager):
        """Test handling of large result sets with limits."""
        sql = "SELECT * FROM employees"
        
        # Test with different limits
        small_results = await test_db_manager.execute_query(sql, max_results=2)
        large_results = await test_db_manager.execute_query(sql, max_results=100)
        
        assert len(small_results) <= 2
        assert len(large_results) <= 100
        assert len(large_results) >= len(small_results)
    
    @pytest.mark.asyncio
    async def test_concurrent_queries(self, test_db_manager):
        """Test concurrent query execution."""
        async def execute_query_task(query_id):
            sql = f"SELECT {query_id} as query_id, * FROM employees LIMIT 1"
            return await test_db_manager.execute_query(sql)
        
        # Execute multiple queries concurrently
        tasks = [execute_query_task(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 5
        for i, result in enumerate(results):
            assert len(result) == 1
            assert result[0]['query_id'] == i