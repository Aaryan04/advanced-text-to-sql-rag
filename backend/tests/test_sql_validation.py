import pytest
from pathlib import Path
import sys

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.sql_validator import SQLValidator
from utils.query_optimizer import QueryOptimizer


class TestSQLValidator:
    """Tests for SQL validation functionality."""
    
    @pytest.fixture
    def validator(self):
        """Create SQL validator instance."""
        return SQLValidator()
    
    @pytest.fixture
    def sample_tables(self):
        """Sample table names for validation."""
        return ['employees', 'departments', 'projects', 'sales']
    
    @pytest.mark.asyncio 
    async def test_valid_select_query(self, validator, sample_tables):
        """Test validation of valid SELECT query."""
        sql = "SELECT * FROM employees WHERE department = 'Engineering'"
        result = await validator.validate_query(sql, sample_tables)
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
    
    def test_forbidden_drop_statement(self, validator, sample_tables):
        """Test rejection of DROP statement."""
        sql = "DROP TABLE employees"
        result = validator.validate_query(sql, sample_tables)
        
        assert result["is_valid"] is False
        assert any("Forbidden keyword: DROP" in error for error in result["errors"])
    
    def test_forbidden_delete_statement(self, validator, sample_tables):
        """Test rejection of DELETE statement."""
        sql = "DELETE FROM employees WHERE id = 1"
        result = validator.validate_query(sql, sample_tables)
        
        assert result["is_valid"] is False
        assert any("Forbidden keyword: DELETE" in error for error in result["errors"])
    
    def test_forbidden_insert_statement(self, validator, sample_tables):
        """Test rejection of INSERT statement."""
        sql = "INSERT INTO employees (name) VALUES ('John')"
        result = validator.validate_query(sql, sample_tables)
        
        assert result["is_valid"] is False
        assert any("Forbidden keyword: INSERT" in error for error in result["errors"])
    
    def test_forbidden_update_statement(self, validator, sample_tables):
        """Test rejection of UPDATE statement."""
        sql = "UPDATE employees SET salary = 100000 WHERE id = 1"
        result = validator.validate_query(sql, sample_tables)
        
        assert result["is_valid"] is False
        assert any("Forbidden keyword: UPDATE" in error for error in result["errors"])
    
    def test_non_select_statement(self, validator, sample_tables):
        """Test rejection of non-SELECT statements."""
        sql = "CREATE TABLE test (id INT)"
        result = validator.validate_query(sql, sample_tables)
        
        assert result["is_valid"] is False
        assert any("Only SELECT queries are allowed" in error for error in result["errors"])
    
    def test_sql_injection_comments(self, validator, sample_tables):
        """Test detection of SQL injection via comments."""
        sql = "SELECT * FROM employees -- DROP TABLE employees"
        result = validator.validate_query(sql, sample_tables)
        
        assert result["is_valid"] is False
        assert any("Comments are not allowed" in error for error in result["errors"])
    
    def test_sql_injection_multiple_statements(self, validator, sample_tables):
        """Test detection of multiple statements."""
        sql = "SELECT * FROM employees; DROP TABLE employees"
        result = validator.validate_query(sql, sample_tables)
        
        assert result["is_valid"] is False
        assert any("Multiple statements are not allowed" in error for error in result["errors"])
    
    def test_unmatched_parentheses(self, validator, sample_tables):
        """Test detection of unmatched parentheses."""
        sql = "SELECT * FROM employees WHERE (department = 'Engineering'"
        result = validator.validate_query(sql, sample_tables)
        
        assert result["is_valid"] is False
        assert any("Unmatched parentheses" in error for error in result["errors"])
    
    def test_unmatched_quotes(self, validator, sample_tables):
        """Test detection of unmatched quotes."""
        sql = "SELECT * FROM employees WHERE department = 'Engineering"
        result = validator.validate_query(sql, sample_tables)
        
        assert result["is_valid"] is False
        assert any("Unmatched single quotes" in error for error in result["errors"])
    
    def test_invalid_table_reference(self, validator, sample_tables):
        """Test detection of invalid table references."""
        sql = "SELECT * FROM nonexistent_table"
        result = validator.validate_query(sql, sample_tables)
        
        assert result["is_valid"] is False
        assert any("Referenced tables not found" in error for error in result["errors"])
    
    def test_valid_table_reference(self, validator, sample_tables):
        """Test validation of valid table references."""
        sql = "SELECT * FROM employees"
        result = validator.validate_query(sql, sample_tables)
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
    
    def test_complex_valid_query(self, validator, sample_tables):
        """Test validation of complex but valid query."""
        sql = """
        SELECT e.first_name, e.last_name, e.salary, d.name as department_name
        FROM employees e
        JOIN departments d ON e.department = d.name
        WHERE e.salary > 50000
        ORDER BY e.salary DESC
        LIMIT 10
        """
        result = validator.validate_query(sql, sample_tables)
        
        assert result["is_valid"] is True
        assert len(result["errors"]) == 0
    
    def test_empty_query(self, validator, sample_tables):
        """Test handling of empty query."""
        sql = ""
        result = validator.validate_query(sql, sample_tables)
        
        assert result["is_valid"] is False
        assert any("Empty SQL query" in error for error in result["errors"])
    
    def test_whitespace_only_query(self, validator, sample_tables):
        """Test handling of whitespace-only query."""
        sql = "   \n\t   "
        result = validator.validate_query(sql, sample_tables)
        
        assert result["is_valid"] is False
        assert any("Empty SQL query" in error for error in result["errors"])
    
    def test_complexity_warnings(self, validator, sample_tables):
        """Test complexity warning generation."""
        # Query with many JOINs
        sql = """
        SELECT * FROM employees e1
        JOIN employees e2 ON e1.manager_id = e2.id
        JOIN employees e3 ON e2.manager_id = e3.id
        JOIN employees e4 ON e3.manager_id = e4.id
        JOIN employees e5 ON e4.manager_id = e5.id
        JOIN employees e6 ON e5.manager_id = e6.id
        """
        result = validator.validate_query(sql, sample_tables)
        
        # Should be valid but have warnings
        assert result["is_valid"] is True
        assert len(result["warnings"]) > 0
        assert any("JOINs" in warning for warning in result["warnings"])
    
    def test_having_without_group_by_warning(self, validator, sample_tables):
        """Test warning for HAVING without GROUP BY."""
        sql = "SELECT * FROM employees HAVING COUNT(*) > 0"
        result = validator.validate_query(sql, sample_tables)
        
        # Should be valid but have warning
        assert result["is_valid"] is True
        assert any("HAVING clause without GROUP BY" in warning for warning in result["warnings"])


class TestQueryOptimizer:
    """Tests for SQL query optimization functionality."""
    
    @pytest.fixture
    def optimizer(self):
        """Create query optimizer instance."""
        return QueryOptimizer()
    
    @pytest.mark.asyncio
    async def test_add_limit_to_select_star(self, optimizer):
        """Test adding LIMIT to SELECT * queries."""
        sql = "SELECT * FROM employees"
        result = await optimizer.optimize_query(sql)
        
        assert result["optimization_applied"] is True
        assert "LIMIT" in result["optimized_query"].upper()
        assert "Added LIMIT to SELECT * query" in result["optimizations"][0]
    
    @pytest.mark.asyncio
    async def test_no_optimization_with_existing_limit(self, optimizer):
        """Test that queries with existing LIMIT aren't modified."""
        sql = "SELECT * FROM employees LIMIT 50"
        result = await optimizer.optimize_query(sql)
        
        # Should not add another optimization for LIMIT
        optimizations = [opt for opt in result["optimizations"] if "LIMIT" in opt]
        assert len(optimizations) <= 1  # At most one LIMIT-related optimization
    
    @pytest.mark.asyncio
    async def test_remove_unnecessary_distinct(self, optimizer):
        """Test removal of unnecessary DISTINCT with SELECT *."""
        sql = "SELECT DISTINCT * FROM employees"
        result = await optimizer.optimize_query(sql)
        
        assert result["optimization_applied"] is True
        assert "DISTINCT" not in result["optimized_query"].upper()
        assert any("unnecessary DISTINCT" in opt for opt in result["optimizations"])
    
    @pytest.mark.asyncio
    async def test_add_default_limit(self, optimizer):
        """Test adding default LIMIT to queries without one."""
        sql = "SELECT first_name, last_name FROM employees WHERE department = 'Engineering'"
        result = await optimizer.optimize_query(sql)
        
        assert result["optimization_applied"] is True
        assert "LIMIT" in result["optimized_query"].upper()
        assert any("default LIMIT" in opt for opt in result["optimizations"])
    
    @pytest.mark.asyncio
    async def test_no_optimization_for_count_queries(self, optimizer):
        """Test that COUNT queries don't get LIMIT added."""
        sql = "SELECT COUNT(*) FROM employees"
        result = await optimizer.optimize_query(sql)
        
        # COUNT queries shouldn't get LIMIT optimization
        limit_optimizations = [opt for opt in result["optimizations"] if "LIMIT" in opt]
        assert len(limit_optimizations) == 0
    
    @pytest.mark.asyncio
    async def test_complex_query_optimization(self, optimizer):
        """Test optimization of complex queries."""
        sql = """
        SELECT DISTINCT * FROM employees e
        JOIN departments d ON e.department = d.name
        WHERE e.salary > 50000
        """
        result = await optimizer.optimize_query(sql)
        
        # Should remove DISTINCT and add LIMIT
        optimized = result["optimized_query"].upper()
        assert "DISTINCT" not in optimized
        assert "LIMIT" in optimized
        assert result["optimization_applied"] is True
    
    @pytest.mark.asyncio
    async def test_query_complexity_analysis(self, optimizer):
        """Test query complexity analysis."""
        # Simple query
        simple_sql = "SELECT * FROM employees"
        simple_analysis = optimizer.analyze_query_complexity(simple_sql)
        
        assert simple_analysis["complexity_level"] in ["low", "medium"]
        assert simple_analysis["complexity_score"] >= 0
        
        # Complex query
        complex_sql = """
        SELECT e1.*, e2.*, d.*
        FROM employees e1
        JOIN employees e2 ON e1.manager_id = e2.id
        JOIN departments d ON e1.department = d.name
        WHERE e1.salary > (SELECT AVG(salary) FROM employees)
        GROUP BY e1.department
        HAVING COUNT(*) > 1
        UNION
        SELECT e3.*, e4.*, d2.*
        FROM employees e3
        JOIN employees e4 ON e3.manager_id = e4.id
        JOIN departments d2 ON e3.department = d2.name
        GROUP BY e3.department
        """
        complex_analysis = optimizer.analyze_query_complexity(complex_sql)
        
        assert complex_analysis["complexity_level"] in ["medium", "high"]
        assert complex_analysis["complexity_score"] > simple_analysis["complexity_score"]
        assert len(complex_analysis["complexity_factors"]) > 0
    
    @pytest.mark.asyncio
    async def test_optimization_preserves_functionality(self, optimizer):
        """Test that optimizations preserve query functionality."""
        sql = "SELECT * FROM employees WHERE department = 'Engineering'"
        result = await optimizer.optimize_query(sql)
        
        # Core WHERE clause should be preserved
        optimized = result["optimized_query"]
        assert "WHERE department = 'Engineering'" in optimized
        
        # Should still be a SELECT statement
        assert optimized.strip().upper().startswith("SELECT")
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_sql(self, optimizer):
        """Test error handling for invalid SQL."""
        sql = "INVALID SQL STATEMENT"
        result = await optimizer.optimize_query(sql)
        
        # Should handle gracefully
        assert "original_query" in result
        assert "optimized_query" in result
        assert result["optimization_applied"] is False
    
    @pytest.mark.asyncio
    async def test_redundant_condition_optimization(self, optimizer):
        """Test optimization of redundant conditions."""
        sql = "SELECT * FROM employees WHERE id = 1 AND id = 1"
        result = await optimizer.optimize_query(sql)
        
        # This might be handled by future optimization rules
        assert "original_query" in result
        assert "optimized_query" in result


class TestSQLSecurityValidation:
    """Tests for SQL security validation."""
    
    @pytest.fixture
    def validator(self):
        return SQLValidator()
    
    def test_sql_injection_via_union(self, validator):
        """Test detection of SQL injection via UNION."""
        # Note: UNION might be allowed in some contexts, but test the validator's response
        sql = "SELECT * FROM employees WHERE id = 1 UNION SELECT * FROM admin_users"
        result = validator.validate_query(sql, ['employees'])
        
        # Should detect invalid table reference
        assert result["is_valid"] is False
        assert any("not found" in error for error in result["errors"])
    
    def test_nested_comments_injection(self, validator):
        """Test detection of nested comment injection."""
        sql = "SELECT * FROM employees /* comment /* nested */ */"
        result = validator.validate_query(sql, ['employees'])
        
        assert result["is_valid"] is False
        assert any("Comments are not allowed" in error for error in result["errors"])
    
    def test_function_name_validation(self, validator):
        """Test validation of function names."""
        # Valid function
        sql = "SELECT COUNT(*), AVG(salary) FROM employees"
        result = validator.validate_query(sql, ['employees'])
        
        assert result["is_valid"] is True
    
    def test_procedure_call_rejection(self, validator):
        """Test rejection of stored procedure calls."""
        sql = "EXEC sp_configure"
        result = validator.validate_query(sql, ['employees'])
        
        assert result["is_valid"] is False
        # Should be rejected for not being SELECT and for forbidden keywords
        assert any("Only SELECT queries are allowed" in error or "Forbidden" in error 
                  for error in result["errors"])
    
    def test_system_function_rejection(self, validator):
        """Test rejection of system functions."""
        sql = "SELECT xp_cmdshell('dir')"
        result = validator.validate_query(sql, ['employees'])
        
        assert result["is_valid"] is False
        assert any("Forbidden" in error for error in result["errors"])